#!/usr/bin/env python3
"""Automated login for PSEG Long Island using Playwright."""

import asyncio
import logging
import time
from typing import Dict, Optional
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class PSEGAutoLogin:
    """Automated login for PSEG Long Island using Playwright."""

    def __init__(self, username: str, password: str):
        """Initialize automated login."""
        self.username = username
        self.password = password
        self.browser = None
        self.page = None
        self.context = None

    async def setup_browser(self):
        """Set up the Playwright browser with stealth techniques."""
        try:
            logger.info("Setting up Playwright browser for automated login...")
            self.playwright = await async_playwright().start()
            
            # Use stealth mode to avoid detection
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with stealth settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            self.page = await self.context.new_page()
            
            # Apply stealth techniques
            await self.page.add_init_script("""
                // Override webdriver property
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({state: Notification.permission}) :
                        originalQuery(parameters)
                );
            """)
            
            logger.info("Playwright browser initialized successfully with stealth techniques")
            return True
        except Exception as e:
            logger.error("Failed to initialize Playwright browser: %s", e)
            return False

    async def get_request_verification_token(self) -> Optional[str]:
        """Get the request verification token from the login page."""
        try:
            logger.info("Getting request verification token from login page...")
            
            # Step 1: Visit main page to establish session
            logger.info("Step 1: Visiting main page to establish session...")
            await self.page.goto("https://mysmartenergy.psegliny.com/")
            await self.page.wait_for_load_state('networkidle')
            
            # Step 2: Wait for page to load and reCAPTCHA to initialize
            logger.info("Step 2: Waiting for page to load and reCAPTCHA to initialize...")
            await asyncio.sleep(3)
            
            # Get page info for debugging
            title = await self.page.title()
            url = self.page.url
            content_length = len(await self.page.content())
            logger.info(f"Current page title: {title}")
            logger.info(f"Current page URL: {url}")
            logger.info(f"Page content length: {content_length} characters")
            logger.info(f"Page content preview (first 500 chars): {await self.page.content()[:500]}")
            
            # Find forms and inputs for debugging
            forms = await self.page.query_selector_all('form')
            inputs = await self.page.query_selector_all('input')
            logger.info(f"Number of forms found: {len(forms)}")
            logger.info(f"Number of inputs found: {len(inputs)}")
            
            # Look for the verification token
            for i, input_elem in enumerate(inputs):
                try:
                    name = await input_elem.get_attribute('name')
                    input_type = await input_elem.get_attribute('type')
                    value = await input_elem.get_attribute('value')
                    logger.info(f"  Input {i}: name='{name}', type='{input_type}', value='{value}'")
                    
                    if name == '__RequestVerificationToken' and value:
                        logger.info(f"✅ Found token in input field")
                        logger.info(f"✅ Got request verification token: {value[:50]}...")
                        return value
                except Exception as e:
                    logger.debug(f"Error reading input {i}: {e}")
                    continue
            
            logger.warning("Could not find request verification token")
            return None
            
        except Exception as e:
            logger.error(f"Error getting request verification token: {e}")
            return None

    async def fill_login_form(self) -> bool:
        """Fill in the login form fields."""
        try:
            logger.info("Filling in login form fields...")
            
            # Wait for form fields to be ready
            logger.info("Waiting for form fields to be ready...")
            await self.page.wait_for_selector('input[name="LoginEmail"]', timeout=10000)
            await self.page.wait_for_selector('input[name="LoginPassword"]', timeout=10000)
            
            # Fill email field
            logger.info(f"Filling email field: {self.username}")
            await self.page.fill('input[name="LoginEmail"]', self.username)
            
            # Fill password field
            logger.info("Filling password field...")
            await self.page.fill('input[name="LoginPassword"]', self.password)
            
            # Verify fields were filled
            email_value = await self.page.input_value('input[name="LoginEmail"]')
            password_value = await self.page.input_value('input[name="LoginPassword"]')
            logger.info(f"Email field value: {email_value}")
            logger.info(f"Password field value: {'*' * len(password_value) if password_value else 'NOT SET'}")
            
            if email_value == self.username and password_value:
                logger.info("✅ Form fields filled successfully")
                return True
            else:
                logger.error("❌ Form fields not filled correctly")
                return False
                
        except Exception as e:
            logger.error(f"Error filling login form: {e}")
            return False

    async def click_login_button(self) -> bool:
        """Click the login button to submit the form."""
        try:
            logger.info("Looking for login button...")
            
            # Look for the login button with various selectors
            login_selectors = [
                'button.btn-primary.loginBtn.g-recaptcha',
                'button.loginBtn',
                'button[type="submit"]',
                'input[type="submit"]'
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = await self.page.query_selector(selector)
                    if login_button:
                        logger.info(f"Found visible login button with selector: {selector}")
                        break
                except:
                    continue
            
            if not login_button:
                logger.error("❌ Could not find login button")
                return False
            
            # Click the login button
            logger.info("Clicking login button...")
            await login_button.click()
            
            logger.info("✅ Login button clicked successfully")
            return True
                    
        except Exception as e:
            logger.error(f"Error in click_login_button: {e}")
            return False

    async def get_fresh_cookies(self) -> Optional[str]:
        """Get fresh cookies using automated login."""
        try:
            logger.info("Starting automated login to get fresh cookies...")
            if not await self.setup_browser():
                return None
            
            logger.info("Getting request verification token...")
            if not await self.get_request_verification_token():
                return None
            
            logger.info("Filling login form...")
            if not await self.fill_login_form():
                return None
            
            logger.info("Clicking login button...")
            if not await self.click_login_button():
                return None
            
            # Wait for successful login (redirect to Dashboard)
            logger.info("Waiting for successful login...")
            try:
                await self.page.wait_for_url("**/Dashboard", timeout=15000)
                logger.info("✅ Successfully logged in and redirected to Dashboard")
            except Exception as e:
                logger.error(f"Failed to redirect to Dashboard: {e}")
                return None
            
            # Get cookies
            cookies = await self.context.cookies()
            logger.info(f"Retrieved {len(cookies)} cookies")
            
            # Format cookies as expected
            cookie_strings = []
            for cookie in cookies:
                if cookie['name'] in ['MM_SID', '__RequestVerificationToken']:
                    cookie_strings.append(f"{cookie['name']}={cookie['value']}")
            
            if len(cookie_strings) >= 2:
                result = "; ".join(cookie_strings)
                logger.info(f"✅ SUCCESS: {result}")
                return result
            else:
                logger.error("❌ Failed to get required cookies")
                return None
            
        except Exception as e:
            logger.error(f"Error in get_fresh_cookies: {e}")
            return None
        finally:
            if self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
            if hasattr(self, 'playwright'):
                try:
                    await self.playwright.stop()
                except:
                    pass

async def get_fresh_cookies(username: str, password: str) -> Optional[str]:
    """Get fresh cookies using automated login."""
    auto_login = PSEGAutoLogin(username, password)
    return await auto_login.get_fresh_cookies()
