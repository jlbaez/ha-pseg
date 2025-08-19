"""The PSEG integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import pytz

from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
)
from homeassistant.components.recorder import get_instance
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_COOKIE
from .pseg import InvalidAuth, PSEGClient
from .auto_login import get_fresh_cookies, check_addon_health

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []

async def get_last_cumulative_kwh(hass: HomeAssistant, statistic_id: str, before_timestamp: datetime) -> float:
    """Get the last recorded cumulative kWh for a given statistic_id BEFORE a specific timestamp."""
    try:
        from homeassistant.components.recorder.statistics import statistics_during_period
        
        # Look for statistics in a window BEFORE our timestamp to find the last cumulative sum
        # Use a 7-day lookback window to ensure we find data even for longer backfills
        lookback_start = before_timestamp - timedelta(days=7)
        
        # Ensure timestamps are timezone-aware for consistent comparison
        if before_timestamp.tzinfo is None:
            before_timestamp = before_timestamp.replace(tzinfo=timezone.utc)
        if lookback_start.tzinfo is None:
            lookback_start = lookback_start.replace(tzinfo=timezone.utc)
        
        try:
            # Get statistics in the lookback window
            stats_in_window = await get_instance(hass).async_add_executor_job(
                statistics_during_period,
                hass,
                lookback_start,  # Start 7 days before our target timestamp
                before_timestamp,  # End at our target timestamp
                [statistic_id],    # Only get our specific statistic
                "hour",            # Hourly granularity
                None,              # No additional filters
                {"start", "sum"}   # Need start time and sum values
            )
        except Exception as e:
            _LOGGER.error("Error calling statistics_during_period: %s", e)
            stats_in_window = None
        
        if stats_in_window and statistic_id in stats_in_window and stats_in_window[statistic_id]:
            # Find the most recent statistic BEFORE our timestamp
            valid_stats = []
            for stat in stats_in_window[statistic_id]:
                if 'sum' in stat and stat['sum'] is not None and 'start' in stat:
                    # Handle both string ISO format and float Unix timestamp
                    if isinstance(stat['start'], str):
                        stat_time = datetime.fromisoformat(stat['start'])
                        # Ensure timezone awareness
                        if stat_time.tzinfo is None:
                            stat_time = stat_time.replace(tzinfo=timezone.utc)
                    elif isinstance(stat['start'], (int, float)):
                        stat_time = datetime.fromtimestamp(stat['start'], tz=timezone.utc)
                    else:
                        _LOGGER.warning("Unexpected start time format: %s (type: %s)", stat['start'], type(stat['start']))
                        continue
                    
                    # Ensure both timestamps are timezone-aware for comparison
                    if stat_time.tzinfo is None:
                        stat_time = stat_time.replace(tzinfo=timezone.utc)
                    
                    if stat_time < before_timestamp:
                        valid_stats.append((stat_time, stat['sum']))
            
            if valid_stats:
                # Sort by time and get the most recent one
                valid_stats.sort(key=lambda x: x[0])
                most_recent_time, most_recent_sum = valid_stats[-1]
                
                _LOGGER.info("Found last cumulative sum: %.6f for %s at %s (before %s)", 
                             most_recent_sum, statistic_id, most_recent_time, before_timestamp)
                return most_recent_sum
            else:
                _LOGGER.info("No valid statistics found before %s for %s", before_timestamp, statistic_id)
                return 0.0
        else:
            _LOGGER.info("No statistics found in lookback window for %s", statistic_id)
            return 0.0
            
    except Exception as e:
        _LOGGER.warning("Could not get last statistics for %s: %s, starting from 0", statistic_id, e)
        return 0.0

async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the PSEG component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PSEG from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Get credentials from config entry
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    cookie = entry.data.get(CONF_COOKIE, "")
    
    if not username or not password:
        _LOGGER.error("No username/password provided")
        return False
    
    # If no cookie available, try to get one from the addon
    if not cookie:
        _LOGGER.info("No cookie available, attempting to get fresh cookies from addon...")
        try:
            cookies = await get_fresh_cookies(username, password)
            
            if cookies:
                # Cookies are already in string format from addon
                cookie_string = cookies
                _LOGGER.info("Successfully obtained fresh cookies from addon")
                
                # Store cookie in config entry for future use
                hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, CONF_COOKIE: cookie_string},
                )
            else:
                _LOGGER.warning("Addon not available or failed to get cookies")
                # Don't fail here - user can provide cookie manually later
        except Exception as e:
            _LOGGER.warning("Failed to get cookies from addon: %s", e)
            # Don't fail here - user can provide cookie manually later
    
    # If we still don't have a cookie, the integration can't function
    if not cookie:
        _LOGGER.error("No cookie available and addon failed to provide one. Please configure a cookie manually.")
        # Create a persistent notification to guide the user
        await hass.async_create_task(
            hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "PSEG Integration: Cookie Required",
                    "message": "No authentication cookie available. Please go to Settings > Integrations > PSEG > Configure to provide a valid cookie.",
                    "notification_id": "psegli_cookie_required",
                },
            )
        )
        return False
    
    # Create client with the available cookie
    client = PSEGClient(cookie)
    hass.data[DOMAIN][entry.entry_id] = client
    
    # Test connection
    try:
        await client.test_connection()
        _LOGGER.info("PSEG connection test successful")
    except InvalidAuth as e:
        _LOGGER.error("Authentication failed: %s", e)
        raise ConfigEntryAuthFailed("Invalid authentication")
    
    # Create coordinator for automatic updates (like Opower)
    coordinator = PSEGCoordinator(hass, entry, client)
    entry.runtime_data = coordinator
    
    # Listen for config changes (when user updates cookie via options)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    # Register manual service for backfilling
    async def async_update_statistics_manual(call: Any) -> None:
        """Manually update statistics table with PSEG data (for backfilling)."""
        days_back = call.data.get("days_back", 0)
        _LOGGER.info("Manual statistics update service (days_back: %d)", days_back)
        
        try:
            # Get the current client instance from hass.data (which gets updated during cookie refresh)
            current_client = hass.data[DOMAIN][entry.entry_id]
            
            # Debug: Log which client we're using and its cookie
            _LOGGER.debug("Manual update using client with cookie: %s", 
                         current_client.cookie[:50] + "..." if len(current_client.cookie) > 50 else current_client.cookie)
            
            # Get fresh data from PSEG with the specified days_back
            historical_data = await current_client.get_usage_data(days_back=days_back)
            
            if "chart_data" in historical_data:
                await _process_chart_data(hass, historical_data["chart_data"])
                _LOGGER.info("Manual statistics update completed successfully")
            else:
                _LOGGER.warning("No chart data found in response")
                
        except InvalidAuth as e:
            _LOGGER.error("Authentication failed during manual update: %s", e)
            _LOGGER.debug("Caught InvalidAuth error: %s (type: %s)", e, type(e))
            
            # Track this failed operation for potential retry
            if hasattr(entry, 'runtime_data') and entry.runtime_data:
                coordinator = entry.runtime_data
                coordinator._last_failed_operation = {"days_back": days_back}
            
            # Try to get fresh cookies from addon if available
            _LOGGER.info("Attempting to refresh expired cookie via addon...")
            
            try:
                # Check if addon is healthy before attempting refresh
                from .auto_login import check_addon_health
                if not await check_addon_health():
                    _LOGGER.info("Addon not available or unhealthy, cannot refresh cookie")
                    return
                
                # Attempt to get fresh cookies
                cookies = await get_fresh_cookies(
                    entry.data.get(CONF_USERNAME), 
                    entry.data.get(CONF_PASSWORD)
                )
                
                if cookies:
                    # Cookies are already in string format from addon
                    cookie_string = cookies
                    
                    # Get the actual client instance from hass.data
                    current_client = hass.data[DOMAIN][entry.entry_id]
                    
                    # Update the client with new cookie
                    current_client.update_cookie(cookie_string)
                    
                    # Also update the coordinator's client if it exists
                    if hasattr(entry, 'runtime_data') and entry.runtime_data:
                        coordinator = entry.runtime_data
                        if hasattr(coordinator, 'client'):
                            coordinator.client.update_cookie(cookie_string)
                            _LOGGER.info("✅ Updated coordinator client cookie")
                    
                    _LOGGER.info("✅ Updated client cookie: %s", cookie_string[:50] + "..." if len(cookie_string) > 50 else cookie_string)
                    _LOGGER.info("✅ Updated client session headers")
                    
                    # Update the config entry
                    hass.config_entries.async_update_entry(
                        entry,
                        data={**entry.data, CONF_COOKIE: cookie_string},
                    )
                    
                    _LOGGER.info("✅ Updated config entry with new cookie")
                    _LOGGER.info("Successfully refreshed cookie via addon")
                    
                    # Test the new cookie
                    try:
                        result = await current_client.test_connection()
                        _LOGGER.info("New cookie validation result: %s", result)
                        if not result:
                            _LOGGER.error("Cookie validation failed - test_connection returned False")
                            raise Exception("Cookie validation failed - test_connection returned False")
                        _LOGGER.info("New cookie validation successful")
                        _LOGGER.info("DEBUG: About to start retry logic...")
                    except Exception as test_err:
                        _LOGGER.error("Cookie validation failed: %s", test_err)
                        raise
                    
                    _LOGGER.info("DEBUG: Connection test completed, now starting retry logic...")
                    
                    # IMPORTANT: Retry the failed operation with the new cookie
                    _LOGGER.info("Retrying failed operation with new cookie...")
                    _LOGGER.debug("Retry: days_back=%d, using client with cookie: %s", 
                                 days_back, current_client.cookie[:50] + "..." if len(current_client.cookie) > 50 else current_client.cookie)
                    try:
                        # Get fresh data from PSEG with the new cookie
                        historical_data = await current_client.get_usage_data(days_back=days_back)
                        
                        if "chart_data" in historical_data:
                            await _process_chart_data(hass, historical_data["chart_data"])
                            _LOGGER.info("Successfully retried operation with new cookie")
                        else:
                            _LOGGER.warning("No chart data found in retry attempt")
                            
                    except Exception as retry_err:
                        _LOGGER.error("Retry attempt failed even with new cookie: %s", retry_err)
                        raise  # Re-raise the error since this is a manual service call
                        
                else:
                    _LOGGER.error("Addon failed to provide fresh cookies")
                    raise  # Re-raise the original InvalidAuth error
                    
            except Exception as refresh_err:
                _LOGGER.error("Failed to refresh cookie: %s", refresh_err)
                raise  # Re-raise the original InvalidAuth error
                
        except Exception as e:
            _LOGGER.error("Failed to update statistics manually: %s", e)
            _LOGGER.debug("Caught generic exception: %s (type: %s)", e, type(e))

    # Register the manual service
    hass.services.async_register(
        DOMAIN,
        "update_statistics",
        async_update_statistics_manual
    )
    
    # Register the cookie refresh service
    async def async_refresh_cookie(call: Any) -> None:
        """Manually refresh the PSEG authentication cookie."""
        _LOGGER.info("Manual cookie refresh service called")
        
        try:
            username = entry.data.get(CONF_USERNAME)
            password = entry.data.get(CONF_PASSWORD)
            
            if not username or not password:
                _LOGGER.error("No credentials available for cookie refresh")
                return
            
            _LOGGER.info("Attempting to refresh cookie via addon...")
            
            # Check if addon is healthy before attempting refresh
            from .auto_login import check_addon_health
            if not await check_addon_health():
                _LOGGER.error("Addon not available or unhealthy, cannot refresh cookie")
                return
            
            # Attempt to get fresh cookies
            cookies = await get_fresh_cookies(username, password)
            
            if cookies:
                # Cookies are already in string format from addon
                cookie_string = cookies
                
                # Get the actual client instance from hass.data
                current_client = hass.data[DOMAIN][entry.entry_id]
                
                # Update the client with new cookie
                current_client.update_cookie(cookie_string)
                
                # Also update the coordinator's client if it exists
                if hasattr(entry, 'runtime_data') and entry.runtime_data:
                    coordinator = entry.runtime_data
                    if hasattr(coordinator, 'client'):
                        coordinator.client.update_cookie(cookie_string)
                        _LOGGER.info("✅ Updated coordinator client cookie")
                
                _LOGGER.info("✅ Updated client cookie: %s", cookie_string[:50] + "..." if len(cookie_string) > 50 else cookie_string)
                _LOGGER.info("✅ Updated client session headers")
                
                # Update the config entry
                hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, CONF_COOKIE: cookie_string},
                )
                
                _LOGGER.info("✅ Updated config entry with new cookie")
                _LOGGER.info("Successfully refreshed cookie via addon")
                
                # Test the new cookie
                await current_client.test_connection()
                _LOGGER.info("New cookie validation successful")
                
                # Create a success notification
                await hass.async_create_task(
                    hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": "PSEG Integration: Cookie Refreshed",
                            "message": "Successfully refreshed your PSEG authentication cookie. The integration should now work properly.",
                            "notification_id": "psegli_cookie_refreshed",
                        },
                    )
                )
                
                # IMPORTANT: If this was called from a failed operation, retry it automatically
                # Check if there's a pending operation to retry
                if hasattr(entry, 'runtime_data') and entry.runtime_data:
                    coordinator = entry.runtime_data
                    if hasattr(coordinator, '_last_failed_operation'):
                        _LOGGER.info("Retrying last failed operation with new cookie...")
                        try:
                            # Retry the last failed operation
                            await coordinator._retry_last_operation()
                            _LOGGER.info("Successfully retried last failed operation with new cookie")
                        except Exception as retry_err:
                            _LOGGER.error("Retry attempt failed even with new cookie: %s", retry_err)
                
            else:
                _LOGGER.error("Addon failed to provide fresh cookies")
                # Create an error notification
                await hass.async_create_task(
                    hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": "PSEG Integration: Cookie Refresh Failed",
                            "message": "Failed to refresh your PSEG authentication cookie. Please check the addon status or provide a cookie manually.",
                            "notification_id": "psegli_cookie_refresh_failed",
                        },
                    )
                )
                
        except Exception as e:
            _LOGGER.error("Failed to refresh cookie: %s", e)
            # Create an error notification
            await hass.async_create_task(
                hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "PSEG Integration: Cookie Refresh Error",
                        "message": f"Error refreshing your PSEG authentication cookie: {e}",
                        "notification_id": "psegli_cookie_refresh_error",
                    },
                )
            )
    
    hass.services.async_register(
        DOMAIN,
        "refresh_cookie",
        async_refresh_cookie
    )
    
    return True

class PSEGCoordinator(DataUpdateCoordinator):
    """Handle fetching PSEG data and updating statistics (like Opower)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: PSEGClient):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="PSEG",
            # Update every 15 minutes to get fresh data
            update_interval=timedelta(minutes=30),
        )
        self.entry = entry
        self.client = client
        self._last_failed_operation = None  # Track the last failed operation for retry

        @callback
        def _dummy_listener() -> None:
            pass

        # Force the coordinator to periodically update by registering at least one listener.
        # Needed when there are no sensors, so _async_update_data still gets called
        # which is needed for _insert_statistics.
        self.async_add_listener(_dummy_listener)

    async def _async_update_data(self):
        """Fetch data from PSEG and update statistics."""
        try:
            # Call the exact same function as manual update to ensure consistency
            # This ensures both manual and automatic updates use identical code paths
            await self.hass.services.async_call(
                DOMAIN,
                "update_statistics",
                {"days_back": 0},
                blocking=True
            )
            
            # Return a simple success indicator since the service handles the actual work
            return {"status": "success"}
                
        except InvalidAuth as e:
            _LOGGER.error("Authentication failed during coordinator update: %s", e)
            
            # Track this failed operation for potential retry
            self._last_failed_operation = {"days_back": 0}
            
            # Try to get fresh cookies from addon if available
            await self._attempt_cookie_refresh()
            
            # Create a persistent notification to alert the user
            await self.hass.async_create_task(
                self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "PSEG Integration: Authentication Failed",
                        "message": f"Your PSEG cookie has expired. Please go to Settings > Integrations > PSEG > Configure to update your cookie.\n\nError: {e}",
                        "notification_id": "psegli_auth_failed",
                    },
                )
            )
            raise UpdateFailed(f"Authentication failed: {e}")
        except Exception as e:
            _LOGGER.error("Failed to update PSEG data: %s", e)
            raise UpdateFailed(f"Failed to update PSEG data: {e}")

    async def _attempt_cookie_refresh(self):
        """Attempt to refresh the cookie using the addon if available and healthy."""
        try:
            _LOGGER.info("Attempting to refresh expired cookie via addon...")
            
            await self.hass.services.async_call(
                DOMAIN,
                "refresh_cookie",
                {},
                blocking=True
            )
            
            _LOGGER.info("Cookie refresh completed via service call")
            
            # After cookie refresh, retry the failed operation
            if self._last_failed_operation:
                _LOGGER.info("Retrying failed operation with new cookie...")
                try:
                    await self._retry_last_operation()
                    _LOGGER.info("Successfully retried failed operation with new cookie")
                    return
                except Exception as retry_err:
                    _LOGGER.error("Retry attempt failed even with new cookie: %s", retry_err)
                    # Let the original UpdateFailed happen
                finally:
                    self._last_failed_operation = None
                
        except Exception as e:
            _LOGGER.error("Failed to refresh cookie via addon: %s", e)

    async def _retry_last_operation(self):
        """Retry the last failed operation."""
        if self._last_failed_operation:
            _LOGGER.info("Retrying last failed operation: %s", self._last_failed_operation)
            try:
                # Retry the last failed operation
                await self.hass.services.async_call(
                    DOMAIN,
                    "update_statistics",
                    self._last_failed_operation,
                    blocking=True
                )
                _LOGGER.info("Successfully retried last failed operation")
                self._last_failed_operation = None  # Clear the failed operation
            except Exception as e:
                _LOGGER.error("Retry attempt failed: %s", e)
                raise
        else:
            _LOGGER.info("No failed operation to retry")

async def _process_chart_data(hass: HomeAssistant, chart_data: dict[str, Any]) -> None:
    """Process chart data and update statistics."""
    # Create timezone once to avoid blocking calls
    local_tz = await hass.async_add_executor_job(pytz.timezone, 'America/New_York')
    
    for series_name, series_data in chart_data.items():
        try:
            _LOGGER.debug("Series %s data type: %s", series_name, type(series_data))
            _LOGGER.debug("Series %s keys: %s", series_name, list(series_data.keys()) if isinstance(series_data, dict) else "not a dict")
            
            valid_points = series_data.get("valid_points", [])
            _LOGGER.debug("Valid points type: %s, length: %s", type(valid_points), len(valid_points) if hasattr(valid_points, '__len__') else "no length")
            
            # Handle case where valid_points might be a string (defensive programming)
            if isinstance(valid_points, str):
                _LOGGER.warning("Valid points is a string, attempting to parse: %s", valid_points[:100])
                try:
                    import json
                    valid_points = json.loads(valid_points)
                    _LOGGER.info("Successfully parsed valid_points from string")
                except Exception as e:
                    _LOGGER.error("Failed to parse valid_points string: %s", e)
                    continue
            
            if not valid_points or not isinstance(valid_points, list):
                _LOGGER.warning("Valid points is not a list: %s", type(valid_points))
                continue
            
            # Determine which statistic this series maps to (using proper format)
            if "Off-Peak" in series_name:
                statistic_id = "psegli:off_peak_usage"  # Use proper format like Opower
            elif "On-Peak" in series_name:
                statistic_id = "psegli:on_peak_usage"   # Use proper format like Opower
            else:
                continue  # Skip non-peak series
            
            # Prepare statistics data for HA's API
            statistics = []
            
            # Check if this series has any meaningful data (non-zero values)
            non_zero_points = [point for point in valid_points if point.get("value", 0) > 0]
            if not non_zero_points:
                _LOGGER.info("Skipping %s - all values are 0, no meaningful data", series_name)
                continue
            
            # Get the first timestamp to determine the hour
            first_timestamp = valid_points[0]["timestamp"] if valid_points else None
            if first_timestamp is None:
                _LOGGER.warning("No valid timestamp found for %s, skipping", series_name)
                continue
                
            # Convert to datetime if it's a timestamp
            if isinstance(first_timestamp, (int, float)):
                first_dt = datetime.fromtimestamp(first_timestamp)
            else:
                first_dt = first_timestamp
                
            # Ensure timezone awareness
            if first_dt.tzinfo is None:
                local_tz = pytz.timezone("America/New_York")
                first_dt = local_tz.localize(first_dt)
            
            # Get the last cumulative sum before our first data point to ensure continuity
            _LOGGER.info("Getting last cumulative sum for %s before %s", series_name, first_dt.strftime("%Y-%m-%d %H:%M"))
            cumulative_offset = await get_last_cumulative_kwh(hass, statistic_id, first_dt)
            
            _LOGGER.info("Starting statistics processing for %s with %d points, continuing from cumulative offset %.6f", 
                         series_name, len(valid_points), cumulative_offset)
            
            # Track how many points we actually process
            points_processed = 0
            
            try:
                for i, point in enumerate(valid_points):
                    try:
                        # Extract timestamp and value from the point
                        if isinstance(point, dict) and "timestamp" in point and "value" in point:
                            timestamp = point["timestamp"]
                            value = point["value"]
                            
                            # Convert timestamp to datetime if it's not already
                            if isinstance(timestamp, (int, float)):
                                timestamp = datetime.fromtimestamp(timestamp)
                            
                            # Ensure we have a timezone-aware datetime
                            if timestamp.tzinfo is None:
                                timestamp = local_tz.localize(timestamp)
                            
                            # Convert to UTC for HA
                            start_time = timestamp.astimezone(timezone.utc)
                            
                            # Check for problematic values before conversion
                            if value is None:
                                _LOGGER.warning("Point %d: value is None, replacing with 0", i)
                                value = 0
                            
                            if isinstance(value, str):
                                try:
                                    raw_energy_value = float(value)
                                except ValueError:
                                    _LOGGER.error("Point %d: cannot convert string value '%s' to float", i, value)
                                    continue
                            else:
                                raw_energy_value = float(value)
                            
                            # Ensure energy value is non-negative
                            energy_value = max(0.0, raw_energy_value)
                            
                            # Additional validation: check for unreasonably large values
                            if energy_value > 1000:  # More than 1000 kWh in an hour is suspicious
                                _LOGGER.warning("Point %d: suspiciously large energy value: %.6f kWh, capping at 100", i, energy_value)
                                energy_value = 100.0
                            
                            # Calculate cumulative total
                            cumulative_kwh = energy_value + cumulative_offset
                            points_processed += 1
                            
                            statistics.append({
                                "start": start_time,        # Time block start
                                "sum": cumulative_kwh,      # Cumulative total
                            })
                            
                            # Update cumulative_offset for the next point
                            cumulative_offset = cumulative_kwh
                            
                        else:
                            _LOGGER.warning("Skipping invalid point %d: %s", i, point)
                            continue
                    except Exception as e:
                        _LOGGER.error("Error processing point %d (%s): %s", i, point, e)
                        continue
                
                _LOGGER.info("Processed %d points for %s", points_processed, series_name)
                
            except Exception as e:
                _LOGGER.error("Error in enumerate loop for series %s: %s", series_name, e)
                continue
            
            # Use HA's Statistics API to update
            try:
                _LOGGER.debug("Calling async_add_external_statistics with %d statistics entries", len(statistics))
                if statistics:
                    _LOGGER.debug("First statistics entry: %s", statistics[0])
                    _LOGGER.debug("Last statistics entry: %s", statistics[-1])
                    _LOGGER.debug("Sample of statistics data being sent:")
                    for i, stat in enumerate(statistics[:3]):  # Show first 3 entries
                        _LOGGER.debug("  Entry %d: %s", i, stat)
                
                # Create metadata for the statistic
                metadata = {
                    "statistic_id": statistic_id,  # Use proper format
                    "source": "psegli",  # Use domain as source
                    "unit_of_measurement": "kWh",
                    "has_mean": False,
                    "has_sum": True,  # Set to True since we're sending cumulative totals
                    "name": f"PSEG {series_name}",
                }
                
                _LOGGER.debug("Using metadata: %s", metadata)
                
                # Check if the function is callable
                if not callable(async_add_external_statistics):
                    _LOGGER.error("async_add_external_statistics is not callable: %s", type(async_add_external_statistics))
                    continue
                
                result = async_add_external_statistics(
                    hass,
                    metadata,
                    statistics
                )
                
                # Check if result is awaitable
                if hasattr(result, '__await__'):
                    await result
                    _LOGGER.info("Successfully updated statistics for %s", statistic_id)
                else:
                    _LOGGER.info("Statistics update completed (non-awaitable result) for %s", statistic_id)
                
                # Verify statistics were stored by checking again
                _LOGGER.debug("Verifying statistics were stored by checking again...")
                try:
                    from homeassistant.components.recorder.statistics import statistics_during_period
                    
                    # Query for the statistics we just stored to verify the sum values
                    end_time = datetime.now()
                    start_time = end_time - timedelta(hours=24)  # Last 24 hours
                    
                    verification_stats = await get_instance(hass).async_add_executor_job(
                        statistics_during_period,
                        hass,
                        start_time,
                        end_time,
                        [statistic_id],  # Only check our specific statistic
                        "hour",
                        None,
                        {"start", "end", "sum"},  # Include sum field
                    )
                    
                    _LOGGER.debug("Verification check returned: %s", verification_stats)
                    
                    if verification_stats and statistic_id in verification_stats and verification_stats[statistic_id]:
                        # Get the last stored statistic with sum value
                        stored_stats = verification_stats[statistic_id]
                        last_stored = None
                        
                        # Find the last entry that has a sum value
                        for stat in reversed(stored_stats):
                            if 'sum' in stat and stat['sum'] is not None:
                                last_stored = stat
                                break
                        
                        if last_stored:
                            last_sum = last_stored.get("sum", 0.0)
                            _LOGGER.info("Verification: Statistics confirmed stored for %s, last sum: %.6f", statistic_id, last_sum)
                        else:
                            _LOGGER.warning("Verification: No sum values found in stored statistics for %s", statistic_id)
                    else:
                        _LOGGER.warning("Verification: No statistics found for %s", statistic_id)
                        
                except Exception as e:
                    _LOGGER.debug("Could not verify statistics: %s", e)
                    
            except Exception as e:
                _LOGGER.error("Error calling async_add_external_statistics for %s: %s", statistic_id, e)
        except Exception as e:
            _LOGGER.error("Error processing series %s: %s", series_name, e)
            continue


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options for PSEG."""
    # Reload the config entry when options change (when user updates cookie)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload the coordinator
    if entry.runtime_data:
        await entry.runtime_data.async_shutdown()
    
    # Remove the services
    hass.services.async_remove(DOMAIN, "update_statistics")
    hass.services.async_remove(DOMAIN, "refresh_cookie")
    
    return True 
