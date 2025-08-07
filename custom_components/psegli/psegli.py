"""PSEG Long Island client."""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, List

import requests
from bs4 import BeautifulSoup

from .const import ATTR_COMPARISON, ATTR_DESCRIPTION, ATTR_LAST_UPDATE
from .exceptions import InvalidAuth

_LOGGER = logging.getLogger(__name__)


class PSEGLIClient:
    """PSEG Long Island API client."""

    def __init__(self, cookie: str) -> None:
        """Initialize the client."""
        self.cookie = cookie
        self.session = requests.Session()
        self.session.headers.update({
            "Cookie": cookie,
            "Referer": "https://id.myaccount.psegliny.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def test_connection(self) -> bool:
        """Test the connection to PSEG."""
        try:
            # First check if we can access the dashboard
            response = self.session.get("https://mysmartenergy.psegliny.com/Dashboard")
            response.raise_for_status()
            
            # Check if we're redirected to login page
            if "login" in response.url.lower() or "signin" in response.url.lower():
                _LOGGER.error("Cookie expired - redirected to login page")
                raise InvalidAuth(
                    "Cookie expired - To get a new cookie:\n"
                    "1. Open Chrome/Firefox Developer Tools (F12)\n"
                    "2. Go to Network tab\n"
                    "3. Visit https://mysmartenergy.psegliny.com\n"
                    "4. Log in to your account\n"
                    "5. Find any request to mysmartenergy.psegliny.com\n"
                    "6. Copy the Cookie header value\n"
                    "7. Go to Home Assistant > Settings > Integrations > PSEG Long Island > Configure\n"
                    "8. Paste the new cookie"
                )
            
            # Now check if we can get widget data
            test_response = self.session.get(
                "https://mysmartenergy.psegliny.com/Widget/LoadWidgets?Region=Usage"
            )
            test_response.raise_for_status()
            
            # Check if the response looks like HTML (indicating login redirect)
            if "<html" in test_response.text.lower():
                _LOGGER.error("Cookie expired - API returning HTML instead of JSON")
                raise InvalidAuth(
                    "Cookie expired - To get a new cookie:\n"
                    "1. Open Chrome/Firefox Developer Tools (F12)\n"
                    "2. Go to Network tab\n"
                    "3. Visit https://mysmartenergy.psegliny.com\n"
                    "4. Log in to your account\n"
                    "5. Find any request to mysmartenergy.psegliny.com\n"
                    "6. Copy the Cookie header value\n"
                    "7. Go to Home Assistant > Settings > Integrations > PSEG Long Island > Configure\n"
                    "8. Paste the new cookie"
                )
            
            # Only try to parse JSON if we didn't get HTML
            try:
                json.loads(test_response.text)
            except json.JSONDecodeError as err:
                _LOGGER.error("Failed to parse API response: %s", err)
                _LOGGER.debug("Response content: %s", test_response.text[:200])  # Log first 200 chars
                raise InvalidAuth("Invalid API response - cookie may be expired") from err
            
            _LOGGER.info("PSEG connection test successful")
            return True
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Failed to connect to PSEG: %s", err)
            raise InvalidAuth("Invalid authentication") from err

    def get_usage_data(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, days_back: int = 0) -> Dict[str, Any]:
        """Get usage data from PSEG."""
        try:
            # First check if our cookie is still valid
            self.test_connection()
            # Calculate date range based on days_back parameter
            if days_back == 0:
                # Yesterday to today (accounting for data lag)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=1)
            else:
                # days_back days ago to now
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
            
            # Get widget data
            widget_response = self.session.get(
                "https://mysmartenergy.psegliny.com/Widget/LoadWidgets?Region=Usage"
            )
            widget_response.raise_for_status()
            widget_data = json.loads(widget_response.text)

            # First, make the Chart/ request to set up the session context and granularity
            chart_setup_url = "https://mysmartenergy.psegliny.com/Dashboard/Chart"
            chart_setup_data = {
                "__RequestVerificationToken": self._get_request_verification_token(),
                "UsageInterval": "5",  # 5 = Hourly granularity
                "UsageType": "1",
                "jsTargetName": "StorageType",
                "EnableHoverChart": "true",
                "Start": start_date.strftime("%Y-%m-%d"),
                "End": end_date.strftime("%Y-%m-%d"),
                "IsRangeOpen": "False",
                "MaintainMaxDate": "true",
                "SelectedViaDateRange": "False",
                "meterIds": ["1501890_0_\"\"_1_1_\"Off-Peak\"_2086517_Delivered", "1501890_0_\"\"_1_1_\"On-Peak\"_2086517_Delivered"],
                "ChartComparison": "1",
                "ChartComparison2": "0",
                "ChartComparison3": "0",
                "ChartComparison4": "0"
            }
            
            _LOGGER.info("Making Chart/ setup request with hourly granularity (days_back: %d, start: %s, end: %s)", 
                        days_back, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            chart_setup_response = self.session.post(chart_setup_url, data=chart_setup_data)
            chart_setup_response.raise_for_status()

            # Then, make the ChartData/ request to get the actual data
            chart_data_url = "https://mysmartenergy.psegliny.com/Dashboard/ChartData"
            chart_data_params = {
                "_": int(datetime.now().timestamp() * 1000)  # Cache buster
            }
            
            _LOGGER.info("Making ChartData/ request to get hourly data")
            chart_response = self.session.get(chart_data_url, params=chart_data_params)
            chart_response.raise_for_status()
            
            # Debug: Log the response content
            _LOGGER.debug("ChartData response status: %s", chart_response.status_code)
            _LOGGER.debug("ChartData response headers: %s", dict(chart_response.headers))
            _LOGGER.debug("ChartData response content (first 500 chars): %s", chart_response.text[:500])
            
            chart_data = json.loads(chart_response.text)

            return self._parse_data(widget_data, chart_data)

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Failed to get usage data: %s", err)
            raise InvalidAuth("Failed to get usage data") from err
        except json.JSONDecodeError as err:
            _LOGGER.error("Failed to parse JSON response: %s", err)
            # This usually indicates an expired cookie (server returns HTML login page instead of JSON)
            _LOGGER.error("This error typically indicates an expired authentication cookie. Please update your cookie in the PSEG integration configuration.")
            raise InvalidAuth("Authentication cookie has expired - please update your cookie") from err

    def _parse_data(self, widget_data: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the widget and chart data."""
        result = {
            "widgets": {},
            "chart_data": {},
            "last_update": datetime.now().isoformat()
        }

        # Parse widget data
        for result_item in widget_data.get("AjaxResults", []):
            if result_item.get("Action") == "Prepend" and "usageWidget" in result_item.get("Value", ""):
                html_content = result_item.get("Value", "")
                soup = BeautifulSoup(html_content, "html.parser")
                
                usage_widgets = soup.find_all("div", class_="usageWidget")
                for widget in usage_widgets:
                    usage_h2 = widget.find("h2")
                    if usage_h2:
                        usage_value = usage_h2.get_text(strip=True)
                        
                        description_div = widget.find("div", class_="widgetDescription")
                        description = description_div.get_text(strip=True) if description_div else ""
                        
                        range_alert = widget.find("div", class_="rangeAlert")
                        comparison = range_alert.get_text(strip=True) if range_alert else ""
                        
                        # Extract numeric value
                        try:
                            numeric_value = float(usage_value.replace("kWh", "").strip())
                        except ValueError:
                            numeric_value = 0.0
                        
                        result["widgets"][description] = {
                            "value": numeric_value,
                            "raw_value": usage_value,
                            "description": description,
                            "comparison": comparison,
                        }

        # Parse chart data
        if "Data" in chart_data and "series" in chart_data["Data"]:
            for series in chart_data["Data"]["series"]:
                series_name = series.get("name", "Unknown")
                data_points = series.get("data", [])
                
                _LOGGER.debug("Processing series: %s with %d data points", series_name, len(data_points))
                
                valid_points = []
                for i, point in enumerate(data_points):
                    if isinstance(point, dict) and "x" in point and "y" in point:
                        timestamp = point["x"] / 1000
                        value = point["y"]
                        if value is not None:
                            # Timestamps need to be shifted by +4 hours to align with actual peak hours
                            # Raw timestamp shows 11:00 AM but should be 3:00 PM for peak hours
                            shifted_timestamp = timestamp + (4 * 3600)  # Add 4 hours
                            local_time = datetime.fromtimestamp(shifted_timestamp)
                            valid_points.append({
                                "timestamp": local_time,
                                "value": value
                            })
                            _LOGGER.debug("Point %d: timestamp=%s, value=%s", i, local_time, value)
                    elif isinstance(point, list) and len(point) >= 2:
                        timestamp = point[0] / 1000
                        value = point[1]
                        if value is not None:
                            # Timestamps need to be shifted by +4 hours to align with actual peak hours
                            # Raw timestamp shows 11:00 AM but should be 3:00 PM for peak hours
                            shifted_timestamp = timestamp + (4 * 3600)  # Add 4 hours
                            local_time = datetime.fromtimestamp(shifted_timestamp)
                            valid_points.append({
                                "timestamp": local_time,
                                "value": value
                            })
                            _LOGGER.debug("Point %d: timestamp=%s, value=%s", i, local_time, value)
                
                if valid_points:
                    latest_point = max(valid_points, key=lambda x: x["timestamp"])
                    values = [p["value"] for p in valid_points]
                    
                    # Debug logging
                    _LOGGER.debug("Series %s: %d valid points, values: %s", 
                                 series_name, len(valid_points), values[:5])
                    
                    result["chart_data"][series_name] = {
                        "latest_value": latest_point["value"],
                        "latest_timestamp": latest_point["timestamp"].isoformat(),
                        "min_value": min(values) if values else 0,
                        "max_value": max(values) if values else 0,
                        "avg_value": sum(values) / len(values) if values else 0,
                        "data_points": len(valid_points),
                        "valid_points": valid_points  # Include the actual data points
                    }

        return result 

    def _get_request_verification_token(self) -> str:
        """Get the request verification token from the main page."""
        try:
            response = self.session.get("https://mysmartenergy.psegliny.com/Dashboard")
            response.raise_for_status()
            
            _LOGGER.debug("Dashboard response status: %s", response.status_code)
            _LOGGER.debug("Dashboard response URL: %s", response.url)
            
            # Parse the HTML to find the verification token
            soup = BeautifulSoup(response.text, "html.parser")
            token_input = soup.find("input", {"name": "__RequestVerificationToken"})
            
            if token_input and token_input.get("value"):
                token = token_input["value"]
                _LOGGER.debug("Found request verification token: %s", token[:20] + "..." if len(token) > 20 else token)
                return token
            else:
                _LOGGER.warning("Could not find request verification token, using empty string")
                return ""
                
        except Exception as e:
            _LOGGER.error("Failed to get request verification token: %s", e)
            return "" 