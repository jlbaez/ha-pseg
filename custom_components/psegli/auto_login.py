#!/usr/bin/env python3
"""Automated login for PSEG Long Island using the automation addon."""

import asyncio
import logging
import aiohttp
from typing import Dict, Optional

logger = logging.getLogger(__name__)

async def check_addon_health() -> bool:
    """Check if the addon is available and healthy."""
    try:
        logger.debug("Checking addon health...")
        
        async with aiohttp.ClientSession() as session:
            # Check if addon is available via direct port access
            try:
                async with session.get("http://localhost:8000/health", timeout=5) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("status") == "healthy":
                            logger.debug("Addon is healthy and available")
                            return True
                        else:
                            logger.debug("Addon responded but status is not healthy")
                            return False
                    else:
                        logger.debug(f"Addon health check failed with status {resp.status}")
                        return False
            except Exception as e:
                logger.debug(f"Addon health check failed: {e}")
                return False
                
    except Exception as e:
        logger.debug(f"Error checking addon health: {e}")
        return False

async def get_fresh_cookies(username: str, password: str) -> Optional[Dict[str, str]]:
    """Get fresh cookies using the automation addon."""
    try:
        logger.info("Requesting fresh cookies from PSEG automation addon...")
        
        # First check if addon is healthy
        if not await check_addon_health():
            logger.warning("Addon not available or unhealthy, cannot get fresh cookies")
            return None
        
        # Try to connect to the addon
        async with aiohttp.ClientSession() as session:
            # Request login via addon
            login_data = {
                "username": username,
                "password": password
            }
            
            async with session.post(
                "http://localhost:8000/login",
                json=login_data,
                timeout=60  # Longer timeout for login process
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("success") and result.get("cookies"):
                        logger.info("Successfully obtained cookies from addon")
                        return result["cookies"]
                    else:
                        logger.error(f"Addon login failed: {result.get('error', 'Unknown error')}")
                        return None
                else:
                    logger.error(f"Addon request failed with status {resp.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"Failed to get cookies from addon: {e}")
        return None
