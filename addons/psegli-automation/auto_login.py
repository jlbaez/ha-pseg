#!/usr/bin/env python3
"""Automated login for PSEG Long Island using Playwright."""

import asyncio
import logging
import time
import random
from typing import Dict, Optional
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

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
            
            # Launch browser with stealth-friendly options (matching working script exactly)
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # Must be True for Docker containers (no X server)
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-popup-blocking',
                    '--disable-web-security',
                    '--allow-running-insecure-content',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-ipc-flooding-protection',
                    '--disable-renderer-backgrounding',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-domain-reliability',
                    '--disable-features=TranslateUI',
                    '--disable-hang-monitor',
                    '--disable-prompt-on-repost',
                    '--disable-sync',
                    '--metrics-recording-only',
                    '--no-default-browser-check',
                    '--safebrowsing-disable-auto-update',
                ]
            )
            
            # Create a new context with stealth (matching working script exactly)
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                # Additional stealth context options
                has_touch=False,
                is_mobile=False,
                device_scale_factor=1,
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                }
            )
            
            self.page = await self.context.new_page()
            
            # Apply comprehensive stealth techniques (matching working script exactly)
            logger.info("Applying comprehensive stealth techniques...")
            
            # Apply playwright-stealth
            stealth_instance = Stealth()
            await stealth_instance.apply_stealth(self.page)
            
            # Additional stealth: Override navigator properties that detect automation
            logger.info("Applying additional stealth overrides...")
            await self.page.add_init_script("""
                // Override properties that detect automation
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Override plugins to look more human
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Override chrome runtime
                window.chrome = {
                    runtime: {},
                };
                
                // Override permissions
                const originalGetProperty = Object.getOwnPropertyDescriptor;
                Object.getOwnPropertyDescriptor = function(obj, prop) {
                    if (prop === 'webdriver') {
                        return undefined;
                    }
                    return originalGetProperty(obj, prop);
                };
            """)
            
            # Add human-like behavior: random scrolling and mouse movements
            logger.info("Adding human-like behavior...")
            try:
                # Random scroll down and up to simulate human reading
                scroll_amount = random.uniform(100, 300)
                await self.page.mouse.wheel(0, scroll_amount)
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await self.page.mouse.wheel(0, -scroll_amount)
                await asyncio.sleep(random.uniform(0.3, 0.8))
                
                # Random mouse movement to simulate human behavior
                await self.page.mouse.move(
                    random.uniform(100, 800),
                    random.uniform(100, 600)
                )
                await asyncio.sleep(random.uniform(0.2, 0.6))
            except Exception as e:
                logger.warning(f"Human-like behavior simulation failed: {e}")
            
            # Set up request monitoring for captcha detection
            await self.setup_request_monitoring()
            
            # Set up console error monitoring
            await self.setup_console_monitoring()
            
            logger.info("✅ Playwright browser initialized successfully")
            return True
        except Exception as e:
            logger.error("Failed to initialize Playwright browser: %s", e)
            return False

    async def setup_request_monitoring(self):
        """Set up request monitoring to detect image captcha requests."""
        try:
            # Monitor requests for reCAPTCHA image captcha patterns
            await self.page.route("**/*", self.handle_request)
            logger.info("Request monitoring set up for captcha detection")
        except Exception as e:
            logger.warning(f"Failed to set up request monitoring: {e}")

    async def setup_console_monitoring(self):
        """Set up console error monitoring."""
        try:
            async def handle_console_error(msg):
                if msg.type == "error":
                    logger.warning("Console error: %s", msg.text)
                elif msg.type == "warning":
                    logger.debug("Console warning: %s", msg.text)
            
            self.page.on("console", handle_console_error)
            logger.info("Console monitoring set up")
        except Exception as e:
            logger.warning(f"Failed to set up console monitoring: {e}")

    async def handle_request(self, route):
        """Handle requests to detect image captcha."""
        try:
            url = route.request.url
            method = route.request.method
            
            # Check for reCAPTCHA image captcha requests
            if "recaptcha" in url.lower() and "google.com" in url.lower():
                logger.info(f"🤖 reCAPTCHA request detected: {method} {url}")
                
                # Only flag actual image captcha challenges, not normal reCAPTCHA flow
                if "api2/payload" in url and "imageselect" in url:
                    logger.error(f"🚨 IMAGE CAPTCHA REQUEST DETECTED: {url}")
                    logger.error(f"🚨 This indicates an image captcha is being loaded!")
                    
                    # Store this as a captcha request
                    self.captcha_request = {
                        'url': url,
                        'method': method,
                        'timestamp': time.time()
                    }
            
            # Continue with the request
            await route.continue_()
            
        except Exception as e:
            logger.debug(f"Error handling request: {e}")
            await route.continue_()

    async def get_request_verification_token(self) -> Optional[str]:
        """Get the request verification token from the login page."""
        try:
            logger.info("Getting request verification token from login page...")
            
            # Step 1: Visit the main page to establish session
            logger.info("Step 1: Visiting main page to establish session...")
            await self.page.goto("https://mysmartenergy.psegliny.com/")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3.5)  # Small delay to let page settle naturally
            
            main_title = await self.page.title()
            main_url = self.page.url
            logger.info("Main page title: %s", main_title)
            logger.info("Main page URL: %s", main_url)
            
            # Step 2: Wait for the page to load and reCAPTCHA to initialize
            logger.info("Step 2: Waiting for page to load and reCAPTCHA to initialize...")
            
            # Wait for the page to be fully loaded and stable
            try:
                logger.info("Waiting for page to reach network idle state...")
                await self.page.wait_for_load_state('networkidle', timeout=30000)
                logger.info("✅ Page reached network idle state")
            except Exception as e:
                logger.warning(f"Network idle timeout, continuing anyway: {e}")
            
            # Additional wait for reCAPTCHA to initialize with human-like timing
            logger.info("Waiting for reCAPTCHA to initialize...")
            wait_time = random.uniform(6, 10)  # Random wait between 6-10 seconds
            logger.info(f"Waiting {wait_time:.1f} seconds (human-like timing)...")
            await asyncio.sleep(wait_time)
            
            current_title = await self.page.title()
            current_url = self.page.url
            content_length = len(await self.page.content())
            logger.info("Current page title: %s", current_title)
            logger.info("Current page URL: %s", current_url)
            logger.info("Page content length: %d characters", content_length)
            logger.info("Page content preview (first 500 chars): %s", (await self.page.content())[:500])
            
            # Debug: Check for forms and inputs
            forms = await self.page.query_selector_all('form')
            inputs = await self.page.query_selector_all('input')
            logger.info("Number of forms found: %d", len(forms))
            logger.info("Number of inputs found: %d", len(inputs))
            
            # Log details about inputs
            for i in range(min(len(inputs), 10)):  # Show first 10 inputs
                try:
                    input_elem = inputs[i]
                    name = await input_elem.get_attribute('name') or 'no-name'
                    input_type = await input_elem.get_attribute('type') or 'no-type'
                    value = await input_elem.get_attribute('value') or 'None'
                    logger.info("  Input %d: name='%s', type='%s', value='%s'", i, name, input_type, value)
                except:
                    pass
            
            # Look for reCAPTCHA elements
            recaptcha_elements = await self.page.query_selector_all('.g-recaptcha, [data-sitekey], iframe[src*="recaptcha"]')
            logger.info("reCAPTCHA elements found: %d", len(recaptcha_elements))
            for i, recaptcha in enumerate(recaptcha_elements):
                try:
                    logger.info("reCAPTCHA %d: %s", i, await recaptcha.get_attribute('class') or 'no-class')
                    
                    # Check for additional reCAPTCHA attributes
                    sitekey = await recaptcha.get_attribute('data-sitekey')
                    if sitekey:
                        logger.info("  reCAPTCHA sitekey: %s", sitekey)
                    
                    # Check if reCAPTCHA is properly initialized
                    try:
                        is_ready = await self.page.evaluate("""
                            () => {
                                if (typeof grecaptcha !== 'undefined') {
                                    return grecaptcha.getResponse() !== '';
                                }
                                return false;
                            }
                        """)
                        logger.info("  reCAPTCHA ready state: %s", is_ready)
                    except Exception as e:
                        logger.warning("  Could not check reCAPTCHA ready state: %s", e)
                        
                except Exception as e:
                    logger.warning("Error examining reCAPTCHA element %d: %s", i, e)
            
            # Check for JavaScript errors that might affect reCAPTCHA
            logger.info("Checking for JavaScript errors...")
            try:
                js_errors = await self.page.evaluate("""
                    () => {
                        if (window.jsErrors && window.jsErrors.length > 0) {
                            return window.jsErrors;
                        }
                        return [];
                    }
                """)
                if js_errors:
                    logger.warning("JavaScript errors found: %s", js_errors)
                else:
                    logger.info("No JavaScript errors detected")
            except Exception as e:
                logger.info("Could not check for JavaScript errors: %s", e)
            
            # Method 1: Look for visible input first
            token = None
            try:
                token_input = await self.page.query_selector('input[name="__RequestVerificationToken"]')
                if token_input:
                    token = await token_input.get_attribute('value')
                    logger.info("✅ Found token in input field")
            except Exception as e:
                logger.warning("Method 1 failed: %s", e)
            
            # Method 2: Look for hidden input
            if not token:
                try:
                    token_input = await self.page.query_selector('input[type="hidden"][name="__RequestVerificationToken"]')
                    if token_input:
                        token = await token_input.get_attribute('value')
                        logger.info("✅ Found token in hidden input field")
                except Exception as e:
                    logger.warning("Method 2 failed: %s", e)
            
            # Method 3: Extract from page HTML
            if not token:
                try:
                    page_content = await self.page.content()
                    # Look for the token in the HTML
                    import re
                    token_match = re.search(r'name="__RequestVerificationToken"\s+value="([^"]+)"', page_content)
                    if token_match:
                        token = token_match.group(1)
                        logger.info("✅ Found token in page HTML")
                except Exception as e:
                    logger.warning("Failed to extract token from HTML: %s", e)
            
            # Method 4: Check if we're already on a different page
            if not token:
                current_url = self.page.url
                logger.info("Current URL: %s", current_url)
                
                # If we're redirected, try to get the token from the current page
                if "login" not in current_url.lower():
                    logger.info("Appears to be redirected, checking current page for token...")
                    try:
                        token_input = await self.page.query_selector('input[name="__RequestVerificationToken"]')
                        if token_input:
                            token = await token_input.get_attribute('value')
                            logger.info("✅ Found token on redirected page")
                    except:
                        pass
            
            if token:
                logger.info("✅ Got request verification token: %s...", token[:20])
                return token
            else:
                logger.error("❌ Could not find request verification token")
                return None
                
        except Exception as e:
            logger.error("Failed to get request verification token: %s", e)
            return None

    async def fill_login_form(self) -> bool:
        """Fill in the login form fields and submit with Enter key."""
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
            
            # Submit form with Enter key (more reliable than clicking button)
            logger.info("Submitting form with Enter key...")
            password_field = await self.page.query_selector('input[name="LoginPassword"]')
            if password_field:
                await password_field.press("Enter")
                logger.info("✅ Enter key pressed - form submitted")
            else:
                logger.error("❌ Could not find password field for Enter key")
                return False
            
            # Wait a moment for the form submission to process
            await asyncio.sleep(2)
            
            logger.info("✅ Form submitted successfully - returning to main flow")
            return True
                
        except Exception as e:
            logger.error(f"Error filling login form: {e}")
            return False



    async def detect_image_captcha(self) -> bool:
        """Detect if an image captcha modal is present."""
        try:
            logger.info("🔍 Checking for image captcha...")
            
            # First check: Have we detected a captcha request?
            if hasattr(self, 'captcha_request') and self.captcha_request:
                logger.error(f"🚨 CAPTCHA REQUEST DETECTED: {self.captcha_request['url']}")
                logger.error("🚨 This indicates an image captcha was loaded - treating as captcha detected")
                return True
            
            # Primary check: Look for the specific instruction text that appears
            try:
                # This is the most reliable indicator - the instruction text
                instruction_elements = await self.page.query_selector_all("div.rc-imageselect-desc-no-canonical")
                if instruction_elements:
                    for element in instruction_elements:
                        if await element.is_visible():
                            text = await element.text_content() or ""
                            if "Select all" in text and ("squares with" in text or "images with" in text):
                                logger.error(f"❌ IMAGE CAPTCHA DETECTED! Text: {text}")
                                return True
            except Exception as e:
                logger.debug(f"Primary instruction check failed: {e}")
            
            # Secondary check: Look for the overall captcha structure
            try:
                payload_elements = await self.page.query_selector_all("div.rc-imageselect-payload")
                if payload_elements:
                    for element in payload_elements:
                        if await element.is_visible():
                            # Double-check by looking for the instruction text within this element
                            try:
                                instruction_text = await element.query_selector("div.rc-imageselect-desc-no-canonical")
                                if instruction_text:
                                    text = await instruction_text.text_content() or ""
                                    if "Select all" in text:
                                        logger.error(f"❌ IMAGE CAPTCHA DETECTED via payload! Text: {text}")
                                        return True
                            except:
                                # If we can't get the text, but the payload is visible, it's likely a captcha
                                logger.error("❌ IMAGE CAPTCHA DETECTED via payload structure!")
                                return True
            except Exception as e:
                logger.debug(f"Secondary payload check failed: {e}")
            
            # Tertiary check: Look for the image grid
            try:
                table_elements = await self.page.query_selector_all("table.rc-imageselect-table")
                if table_elements:
                    for element in table_elements:
                        if await element.is_visible():
                            logger.error("❌ IMAGE CAPTCHA DETECTED via image grid!")
                            return True
            except Exception as e:
                logger.debug(f"Tertiary table check failed: {e}")
            
            logger.info("✅ No image captcha detected")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error detecting image captcha: {e}")
            # If we can't detect, assume no captcha to avoid false positives
            return False

    async def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.browser:
                await self.browser.close()
                logger.info("Browser closed")
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
        
        try:
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
                logger.info("Playwright stopped")
        except Exception as e:
            logger.warning(f"Error stopping playwright: {e}")

    async def get_fresh_cookies(self) -> Optional[str]:
        """Get fresh cookies using automated login with retry logic."""
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"🔄 Attempt {attempt}: Starting automated login to get fresh cookies...")
                if not await self.setup_browser():
                    logger.error(f"❌ Failed to setup browser on attempt {attempt}")
                    continue
                
                try:
                    logger.info("Getting request verification token...")
                    if not await self.get_request_verification_token():
                        logger.error(f"❌ Failed to get request verification token on attempt {attempt}")
                        continue
                    
                    logger.info("Filling login form...")
                    if not await self.fill_login_form():
                        logger.error("❌ Login form submission failed (likely due to image captcha)")
                        continue
                    
                    # Check for image captcha after form submission
                    logger.info("🔍 Checking for image captcha after form submission...")
                    if await self.detect_image_captcha():
                        logger.error("❌ Image captcha appeared after form submission - failing fast")
                        continue
                    
                    # Wait for successful login (redirect to Dashboard)
                    logger.info("Waiting for successful login...")
                    try:
                        await self.page.wait_for_url("**/Dashboard", timeout=30000)
                        logger.info("✅ Successfully logged in and redirected to Dashboard")
                    except Exception as e:
                        logger.error(f"Failed to redirect to Dashboard: {e}")
                        continue
                    
                    # Get cookies
                    cookies = await self.context.cookies()
                    logger.info(f"Retrieved {len(cookies)} cookies")
                    
                    # Format cookies as expected - MM_SID must come FIRST
                    cookie_strings = []
                    for cookie in cookies:
                        if cookie['name'] in ['MM_SID', '__RequestVerificationToken']:
                            cookie_strings.append(f"{cookie['name']}={cookie['value']}")
                    
                    if len(cookie_strings) >= 2:
                        # Ensure MM_SID is first, then __RequestVerificationToken
                        ordered_cookies = []
                        for cookie in cookie_strings:
                            if cookie.startswith('MM_SID='):
                                ordered_cookies.insert(0, cookie)  # Put MM_SID first
                            elif cookie.startswith('__RequestVerificationToken='):
                                ordered_cookies.append(cookie)  # Put RequestVerificationToken second
                        
                        result = "; ".join(ordered_cookies)
                        logger.info(f"🎉 LOGIN SUCCESSFUL - Returning cookies immediately!")
                        logger.info(f"✅ SUCCESS: {result}")
                        return result
                    else:
                        logger.error(f"❌ Failed to get required cookies on attempt {attempt}")
                        continue
                        
                finally:
                    # Always cleanup browser
                    await self.cleanup()
                    
            except Exception as e:
                logger.error(f"❌ Error on attempt {attempt}: {e}")
                try:
                    await self.cleanup()
                except Exception as cleanup_error:
                    logger.warning(f"Cleanup error: {cleanup_error}")
                
                # If this is the last attempt, don't continue
                if attempt == max_attempts:
                    break
                    
                # Wait a bit before retrying
                logger.info(f"⏳ Waiting 2 seconds before retry...")
                await asyncio.sleep(2)
                continue
        
        logger.error("❌ All attempts failed")
        return None

async def get_fresh_cookies(username: str, password: str) -> Optional[str]:
    """Get fresh cookies using automated login."""
    auto_login = PSEGAutoLogin(username, password)
    return await auto_login.get_fresh_cookies()
