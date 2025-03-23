"""
Browser control module using Selenium WebDriver for MindRoot browser use plugin
"""
import asyncio
import base64
import logging
import re
import os
import time
import tempfile
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, TimeoutException
import traceback

# Tab handling
from .tab_handler import get_tab_handler, integrate_tab_handler

logger = logging.getLogger(__name__)

# Global session storage
_browser_sessions = {}

class BrowserClient:
    """
    Manages browser interaction using Selenium WebDriver
    """
    def __init__(self, driver, session_id):
        self.driver = driver
        self.session_id = session_id
        # Initialize tab handler (will be lazily loaded when needed)
        self.tab_handler = None
        self.start_time = time.time()
    
    async def navigate_to(self, url):
        """Navigate to specified URL"""
        try:
            self.driver.get(url)
            return {"status": "ok", "url": url}
        except WebDriverException as e:
            logger.error(f"Navigation error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_screenshot(self):
        """Capture screenshot as PIL Image"""
        try:
            screenshot = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot))
            return image
        except WebDriverException as e:
            logger.error(f"Screenshot error: {str(e)}")
            return None
    
    async def click_element(self, element_id):
        """Click element by ID from element map"""
        try:
            # Run the getElementByBrowserUseId function to get the element
            script = f"""
            return window.browserUseElements[{element_id}];
            """
            element = self.driver.execute_script(script)
            if element:
                element.click()
                return {"status": "ok", "message": f"Clicked element {element_id}"}
            return {"status": "error", "message": f"Element {element_id} not found"}
        except Exception as e:
            logger.error(f"Click error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def type_text(self, element_id, text):
        """Type text into an element by ID"""
        try:
            # Run the getElementByBrowserUseId function to get the element
            script = f"""
            return window.browserUseElements[{element_id}];
            """
            element = self.driver.execute_script(script)
            if element:
                element.send_keys(text)
                return {"status": "ok", "message": f"Typed text into element {element_id}"}
            return {"status": "error", "message": f"Element {element_id} not found"}
        except Exception as e:
            logger.error(f"Type text error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def hover(self, element_id):
        """Hover over an element by ID"""
        try:
            script = f"""
            return window.browserUseElements[{element_id}];
            """
            element = self.driver.execute_script(script)
            if element:
                actions = ActionChains(self.driver)
                actions.move_to_element(element).perform()
                return {"status": "ok", "message": f"Hovered over element {element_id}"}
            return {"status": "error", "message": f"Element {element_id} not found"}
        except Exception as e:
            logger.error(f"Hover error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def right_click(self, element_id):
        """Right-click on an element by ID"""
        try:
            script = f"""
            return window.browserUseElements[{element_id}];
            """
            element = self.driver.execute_script(script)
            if element:
                actions = ActionChains(self.driver)
                actions.context_click(element).perform()
                return {"status": "ok", "message": f"Right-clicked on element {element_id}"}
            return {"status": "error", "message": f"Element {element_id} not found"}
        except Exception as e:
            logger.error(f"Right-click error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    async def double_click(self, element_id):
        """Double-click on an element by ID"""
        try:
            script = f"""
            return window.browserUseElements[{element_id}];
            """
            element = self.driver.execute_script(script)
            if element:
                actions = ActionChains(self.driver)
                actions.double_click(element).perform()
                return {"status": "ok", "message": f"Double-clicked on element {element_id}"}
            return {"status": "error", "message": f"Element {element_id} not found"}
        except Exception as e:
            logger.error(f"Double-click error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def set_checkbox(self, element_id, checked=True):
        """Check or uncheck a checkbox by ID"""
        try:
            script = f"""
            const element = window.browserUseElements[{element_id}];
            if (element) {{
                if (element.checked !== {str(checked).lower()}) {{
                    element.click(); // Toggle the current state
                }}
                return true;
            }}
            return false;
            """
            result = self.driver.execute_script(script)
            if result:
                return {"status": "ok", "message": f"Set checkbox {element_id} to {checked}"}
            return {"status": "error", "message": f"Element {element_id} not found or not a checkbox"}
        except Exception as e:
            logger.error(f"Set checkbox error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def select_option(self, element_id, option_text=None, option_value=None):
        """Select an option from a dropdown by ID"""
        try:
            # First get the select element by ID
            script = f"""
            return window.browserUseElements[{element_id}];
            """
            select_element = self.driver.execute_script(script)
            
            if not select_element:
                return {"status": "error", "message": f"Element {element_id} not found"}
            
            # Use Selenium's Select class to interact with it
            from selenium.webdriver.support.ui import Select
            select = Select(select_element)
            
            if option_text is not None:
                select.select_by_visible_text(option_text)
                return {"status": "ok", "message": f"Selected option with text '{option_text}'"}
            elif option_value is not None:
                select.select_by_value(option_value)
                return {"status": "ok", "message": f"Selected option with value '{option_value}'"}
            else:
                return {"status": "error", "message": "Either option_text or option_value must be provided"}
        except Exception as e:
            logger.error(f"Select option error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def drag_and_drop(self, source_id, target_id):
        """Drag and drop one element to another by IDs"""
        try:
            # Get both elements by their IDs
            script = f"""
            return [window.browserUseElements[{source_id}], window.browserUseElements[{target_id}]];
            """
            elements = self.driver.execute_script(script)
            if len(elements) != 2 or None in elements:
                return {"status": "error", "message": "Source or target element not found"}
                
            source_element, target_element = elements
            
            # Perform drag and drop
            actions = ActionChains(self.driver)
            actions.drag_and_drop(source_element, target_element).perform()
            return {"status": "ok", "message": f"Dragged element {source_id} to element {target_id}"}
        except Exception as e:
            logger.error(f"Drag and drop error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_text(self, element_id):
        """Get the text content of an element by ID"""
        try:
            script = f"""
            const element = window.browserUseElements[{element_id}];
            return element ? element.textContent.trim() : null;
            """
            text = self.driver.execute_script(script)
            if text is not None:
                return {"status": "ok", "text": text}
            return {"status": "error", "message": f"Element {element_id} not found"}
        except Exception as e:
            logger.error(f"Get text error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_attribute(self, element_id, attribute_name):
        """Get the value of an element's attribute by ID"""
        try:
            script = f"""
            const element = window.browserUseElements[{element_id}];
            return element ? element.getAttribute('{attribute_name}') : null;
            """
            value = self.driver.execute_script(script)
            if value is not None:  # Note: attribute might legitimately be empty string
                return {"status": "ok", "value": value}
            return {"status": "error", "message": f"Element {element_id} not found"}
        except Exception as e:
            logger.error(f"Get attribute error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def press_key(self, key):
        """Press a keyboard key"""
        try:
            # Map common key names to Selenium Keys
            key_map = {
                "enter": Keys.ENTER,
                "tab": Keys.TAB,
                "escape": Keys.ESCAPE,
                "esc": Keys.ESCAPE,
                "space": Keys.SPACE,
                "backspace": Keys.BACK_SPACE,
                "delete": Keys.DELETE,
                "arrow_up": Keys.ARROW_UP,
                "arrow_down": Keys.ARROW_DOWN,
                "arrow_left": Keys.ARROW_LEFT,
                "arrow_right": Keys.ARROW_RIGHT,
                "home": Keys.HOME,
                "end": Keys.END,
                "page_up": Keys.PAGE_UP,
                "page_down": Keys.PAGE_DOWN,
            }
            
            # Get the key to press
            key_to_press = key_map.get(key.lower(), key)
            
            # Get the active element and send the key
            actions = ActionChains(self.driver)
            actions.send_keys(key_to_press).perform()
            
            return {"status": "ok", "message": f"Pressed key: {key}"}
        except Exception as e:
            logger.error(f"Press key error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def key_combination(self, keys):
        """Press a combination of keys"""
        try:
            # Map common key names to Selenium Keys
            key_map = {
                "ctrl": Keys.CONTROL,
                "alt": Keys.ALT,
                "shift": Keys.SHIFT,
                "command": Keys.COMMAND,
                "enter": Keys.ENTER,
                "tab": Keys.TAB,
                "escape": Keys.ESCAPE,
                "space": Keys.SPACE,
                "a": "a",
                "c": "c",
                "v": "v",
                "x": "x",
                "z": "z",
            }
            
            # Parse the keys to press
            if isinstance(keys, str):
                keys = keys.split("+")
            
            # Convert keys to Selenium Keys
            keys_to_press = [key_map.get(k.lower(), k) for k in keys]
            
            # Press the key combination
            actions = ActionChains(self.driver)
            for key in keys_to_press[:-1]:
                actions.key_down(key)
            
            actions.key_down(keys_to_press[-1])
            actions.key_up(keys_to_press[-1])
            
            for key in reversed(keys_to_press[:-1]):
                actions.key_up(key)
                
            actions.perform()
            
            return {"status": "ok", "message": f"Pressed key combination: {'+'.join(keys)}"}
        except Exception as e:
            logger.error(f"Key combination error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def scroll(self, direction="down", amount=300):
        """Scroll the page in the specified direction"""
        try:
            # Map direction to JavaScript scroll parameters
            scroll_map = {
                "down": (0, amount),
                "up": (0, -amount),
                "right": (amount, 0),
                "left": (-amount, 0),
            }
            
            x_scroll, y_scroll = scroll_map.get(direction.lower(), (0, amount))
            
            # Execute JavaScript to scroll
            script = f"""
            window.scrollBy({x_scroll}, {y_scroll});
            return true;
            """
            self.driver.execute_script(script)
            
            return {"status": "ok", "message": f"Scrolled {direction} by {amount} pixels"}
        except Exception as e:
            logger.error(f"Scroll error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def scroll_to_element(self, element_id):
        """Scroll to make an element visible"""
        try:
            script = f"""
            const element = window.browserUseElements[{element_id}];
            if (element) {{
                element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                return true;
            }}
            return false;
            """
            result = self.driver.execute_script(script)
            
            if result:
                return {"status": "ok", "message": f"Scrolled to element {element_id}"}
            return {"status": "error", "message": f"Element {element_id} not found"}
        except Exception as e:
            logger.error(f"Scroll to element error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def go_back(self):
        """Navigate back in browser history"""
        try:
            self.driver.back()
            return {"status": "ok", "message": "Navigated back"}
        except Exception as e:
            logger.error(f"Go back error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def go_forward(self):
        """Navigate forward in browser history"""
        try:
            self.driver.forward()
            return {"status": "ok", "message": "Navigated forward"}
        except Exception as e:
            logger.error(f"Go forward error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def refresh(self):
        """Refresh the current page"""
        try:
            self.driver.refresh()
            return {"status": "ok", "message": "Page refreshed"}
        except Exception as e:
            logger.error(f"Refresh error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def update_state(self):
        """Update browser state and identify interactive elements"""
        try:
            # Execute DOM analysis JavaScript
            with open(os.path.join(os.path.dirname(__file__), "static/js/dom-analyzer.js"), "r") as f:
                script = f.read()

            # Add script execution wrapper
            exec_script = """
            // Initialize global element storage
            window.browserUseElements = {};
            
            // Execute analyzer
            return (() => {
                // DOM Analyzer script is inserted here (see dom-analyzer.js)
                %s
                
                // Run the function
                return findInteractiveElements({
                    highlightElements: true,
                    viewportExpansion: 0
                });
            })();
            """ % script
            
            elements = self.driver.execute_script(exec_script)
            
            # Take a screenshot to include in the state
            screenshot = await self.get_screenshot()
            
            return {
                "status": "ok",
                "url": self.driver.current_url,
                "title": self.driver.title,
                "elements": elements,
                "screenshot": screenshot
            }
        except Exception as e:
            logger.error(f"State update error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def ensure_tab_handler(self):
        """Ensure tab handler is initialized"""
        print(f"DEBUG [ensure_tab_handler] Called, current tab_handler: {self.tab_handler}")
        if self.tab_handler is None:
            try:
                print("DEBUG [ensure_tab_handler] Tab handler is None, attempting to create one")
                self.tab_handler = await get_tab_handler(self)
                if self.tab_handler is None:
                    logger.error("Failed to initialize tab handler")
                    return False
                print(f"DEBUG [ensure_tab_handler] Created tab_handler: {self.tab_handler}, now integrating")
                from .tab_handler import integrate_tab_handler
                await integrate_tab_handler(self)
            except Exception as e:
                logger.error(f"Tab handler initialization error: {str(e)}")
                return False
        return True
    async def click_element_and_handle_new_tab(self, element_id):
        """Click element and handle new tab if one opens
        
        This will click an element, detect if a new tab opens, and
        automatically switch to that new tab if one is detected.
        """
        if not await self.ensure_tab_handler():
            return {"status": "error", "message": "Tab handler initialization failed"}
            
        # Use the tab handler to handle the click and potential tab switch
        return await self.tab_handler.click_and_switch_if_new_tab(element_id)

    async def get_all_tabs(self):
        """Get information about all open tabs
        
        Returns:
            List of dictionaries with tab information
        """
        if not await self.ensure_tab_handler():
            return {"status": "error", "message": "Tab handler initialization failed"}
            
        return await self.tab_handler.get_all_tabs()
    
    async def switch_to_tab(self, window_handle):
        """Switch to a specific tab by window handle
        
        Args:
            window_handle: The handle of the window to switch to
            
        Returns:
            Status and information about the tab
        """
        if not await self.ensure_tab_handler():
            return {"status": "error", "message": "Tab handler initialization failed"}
            
        return await self.tab_handler.switch_to_tab(window_handle)
    
    async def switch_to_newest_tab(self):
        """Switch to the most recently opened tab
        
        Returns:
            Status and information about the tab
        """
        if not await self.ensure_tab_handler():
            return {"status": "error", "message": "Tab handler initialization failed"}
            
        return await self.tab_handler.switch_to_newest_tab()
    
    async def switch_to_original_tab(self):
        """Switch back to the original tab
        
        Returns:
            Status and information about the tab
        """
        if not await self.ensure_tab_handler():
            return {"status": "error", "message": "Tab handler initialization failed"}
            
        return await self.tab_handler.switch_to_original_tab()

    async def close_current_tab(self):
        """Close the current tab and switch to another open tab
        
        Returns:
            Status and information about the new current tab
        """
        if not await self.ensure_tab_handler():
            return {"status": "error", "message": "Tab handler initialization failed"}
            
        # Use the tab handler to close the current tab
        return await self.tab_handler.close_current_tab()

async def check_browser_dependencies():
    """Check if required dependencies for browser control are available"""
    try:
        loop = asyncio.get_event_loop()
        # Run a simple function that creates a Chrome options object
        # to verify undetected-chromedriver is working
        await loop.run_in_executor(None, uc.ChromeOptions)
        return {"status": "ok", "message": "Browser dependencies with anti-detection features are available"}
    except Exception as e:
        logger.error(f"Dependency check failed: {str(e)}")
        return {"status": "error", "message": f"Browser dependencies not available: {str(e)}"}

def detect_chrome_version():
    """Detect the installed Chrome/Chromium version.
    
    Returns:
        int: The major version number of Chrome, or None if detection fails.
    """
    try:
        # Try various commands to detect Chrome version
        commands = [
            # Linux Chrome
            ["google-chrome", "--version"],
            # Linux Chromium
            ["chromium-browser", "--version"],
            ["chromium", "--version"],
            # macOS
            ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
            # Windows (requires shell=True which we handle separately)
        ]
        
        for cmd in commands:
            try:
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
                logger.info(f"Chrome version check output: {output}")
                # Extract version number (e.g., "Google Chrome 133.0.6943.53" -> "133")
                match = re.search(r'\b(\d+)\.(\d+\.\d+\.\d+)\b', output)
                if match:
                    major_version = int(match.group(1))
                    logger.info(f"Detected Chrome major version: {major_version}")
                    return major_version
            except (subprocess.SubprocessError, OSError, ValueError):
                continue
        
        # Windows specific approach
        if os.name == 'nt':
            try:
                output = subprocess.check_output(
                    'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
                    shell=True, text=True
                )
                match = re.search(r'\b(\d+)\.(\d+\.\d+\.\d+)\b', output)
                if match:
                    major_version = int(match.group(1))
                    logger.info(f"Detected Chrome major version from registry: {major_version}")
                    return major_version
            except (subprocess.SubprocessError, OSError, ValueError):
                pass
    except Exception as e:
        logger.warning(f"Error detecting Chrome version: {e}")
    
    # Default if detection fails
    logger.warning("Could not detect Chrome version, will let undetected-chromedriver auto-detect")
    return None

async def get_browser_client(context=None):
    """Get or create browser client"""
    # If context is provided, try to get user-specific browser
    user_id = None
    if context and hasattr(context, "user") and context.user:
        user_id = context.user
    
    session_id = f"browser_{user_id}" if user_id else "browser_default"
    
    # Return existing session if available
    if session_id in _browser_sessions:
        return _browser_sessions[session_id]
    
    # If no session exists, create a new one
    return await start_browser(context)

async def start_browser(context=None):
    """Start a new browser session"""
    # Get user ID for session tracking
    user_id = None
    if context and hasattr(context, "user") and context.user:
        user_id = context.user
    
    session_id = f"browser_{user_id}" if user_id else "browser_default"
    
    # Check if a session already exists
    if session_id in _browser_sessions:
        logger.info(f"Browser session {session_id} already exists")
        return {"status": "ok", "message": "Browser is already running"}
   
    # TODO: try this:
    try:
        # Create and configure WebDriver
        loop = asyncio.get_event_loop()
        
        # Debug: Print display environment variable
        logger.info(f"DISPLAY environment variable: {os.environ.get('DISPLAY', 'Not set')}")
        
        # Detect Chrome version before creating the driver
        chrome_version = await loop.run_in_executor(None, detect_chrome_version)
        logger.info(f"Using Chrome version: {chrome_version or 'auto-detect'}") 
        
        def create_driver():
            chrome_version = os.environ.get('CHROME_VERSION', 133)
            # Create a temporary directory for Chrome data
            # Using a fresh directory for each session can help avoid profile issues
            data_dir = tempfile.mkdtemp(prefix="mr_browser_chrome_")
            os.makedirs(data_dir, exist_ok=True)
            
            logger.info(f"Using temporary Chrome profile directory: {data_dir}")
            
            # Create undetected_chromedriver options
            options = uc.ChromeOptions()
            
            # Add standard arguments for stability
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Set headless mode - Comment the next line out for interactive mode
            # Using argument method instead of property for better compatibility
            # options.add_argument('--headless=new')  # For headless mode
            
            # Do NOT use options.headless property as it may cause issues with
            # undetected-chromedriver in some versions
            # options.headless = True  # This can cause problems, use argument instead
            
            
            # Anti-detection measures
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-infobars')
            
            # Set window size - important for consistent behavior
            options.add_argument('--window-size=1920,1080')
            
            # Better way to handle user agent if needed
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36')
            
            # Use a custom user data directory to avoid profile conflicts
            options.add_argument(f'--user-data-dir={data_dir}')
            
            # Try setting display explicitly if not set
            if not os.environ.get('DISPLAY'):
                os.environ['DISPLAY'] = ':0'
                
            # Check if headless mode is enabled by looking for the argument
            is_headless = False
            for arg in options.arguments:
                if '--headless' in arg:
                    is_headless = True
                    break
            
            # Additional arguments that can help with stability in interactive mode
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-gpu')
            
            # Log the browser mode
            logger.info(f"Starting Chrome in {'headless' if is_headless else 'interactive'} mode")
            
            # Add remote debugging port - this can help with interactive mode stability
            # by ensuring Chrome doesn't freeze when connecting
            options.add_argument('--remote-debugging-port=9222')
            
            from webdriver_manager.chrome import ChromeDriverManager
            
            try:
                # Try with driver manager path
                driver_exec_path = ChromeDriverManager().install() 
                
                # Create driver with or without version specification
                if chrome_version:
                    driver = uc.Chrome(
                        options=options, 
                        driver_executable_path=driver_exec_path,
                        version_main=chrome_version  # Use detected version
                    )
                    # Allow time for browser initialization
                    time.sleep(2)
                else:
                    driver = uc.Chrome(
                        options=options, 
                        driver_executable_path=driver_exec_path
                    )
                    # Allow time for browser initialization
                    time.sleep(2)
                logger.info("Successfully created driver with webdriver_manager path")
                logger.info(f"Browser PID: {driver.service.process.pid if hasattr(driver.service, 'process') else 'Unknown'}")
                return driver
            except Exception as e:
                logger.warning(f"Failed with webdriver_manager: {e}, trying direct approach")
                
                # Set window size before creating the fallback driver
                try:                    
                    # If that fails, try direct approach without driver_executable_path
                    # Create a fresh ChromeOptions object to avoid reuse issues
                    fresh_options = uc.ChromeOptions()
                    fresh_options.add_argument('--no-sandbox')
                    fresh_options.add_argument('--disable-dev-shm-usage')
                    fresh_options.add_argument('--disable-blink-features=AutomationControlled')
                    # Keep extensions enabled as disabling them sometimes causes issues
                    fresh_options.add_argument('--disable-infobars')
                    
                    # Set window size
                    fresh_options.add_argument('--window-size=1920,1080')
                    
                    # Add user agent to help avoid detection
                    fresh_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36')
                    
                    # Additional arguments for stability
                    fresh_options.add_argument('--no-first-run')
                    fresh_options.add_argument('--no-default-browser-check')
                    fresh_options.add_argument('--disable-gpu')
                    
                    # Add remote debugging port - often helps with stability in interactive mode
                    fresh_options.add_argument('--remote-debugging-port=9222')
                    
                    
                    fresh_options.add_argument(f'--user-data-dir={data_dir}')
                    is_headless = False  # Track headless state for logging
                    
                    # IMPORTANT: Uncomment the next line for headless mode
                    # If interactive mode freezes, try enabling headless mode
                    # fresh_options.add_argument('--headless=new')
                    # if uncommented: is_headless = True
                    
                    # if uncommented: is_headless = True
                    
                    logger.info(f"Starting Chrome in {'headless' if is_headless else 'interactive'} mode (fallback)")
                    # fresh_options.add_argument('--headless=new')
                    
                    # Use the fresh options object
                    # Create driver with or without version specification
                    chrome_version = 133
                    if chrome_version:
                        driver = uc.Chrome(
                            options=fresh_options,
                            version_main=chrome_version  # Use detected version
                        )
                        # Allow time for browser initialization
                        time.sleep(2)
                        logger.info(f"Browser PID: {driver.service.process.pid if hasattr(driver.service, 'process') else 'Unknown'}")
                        logger.info("Successfully created driver with direct approach (with version)")
                    else:
                        driver = uc.Chrome(
                            options=fresh_options
                        )
                        # Allow time for browser initialization
                        time.sleep(2)
                        logger.info(f"Browser PID: {driver.service.process.pid if hasattr(driver.service, 'process') else 'Unknown'}")
                        logger.info("Successfully created driver with direct approach (no version)")
                    return driver
                except Exception as e2:
                    logger.error(f"Both driver creation methods failed: {e2}")
                    raise e2
            
        # Create the driver
        try:
            driver = await loop.run_in_executor(None, create_driver)
            
            # Create client and store in session
            client = BrowserClient(driver, session_id)
            _browser_sessions[session_id] = client
            
            # Initialize tab handler
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: None)  # Small delay for browser to stabilize
            print(f"DEBUG [start_browser] About to integrate tab handler for client: {client}")
            await integrate_tab_handler(client)
            print(f"DEBUG [start_browser] Tab handler integration complete, tab_handler: {client.tab_handler}")
            
            logger.info(f"Started browser session {session_id}")
            return {"status": "ok", "message": "Browser started successfully"}
        except Exception as e:
            full_error = f"Failed to start browser: {str(e)}\n{traceback.format_exc()}"
            logger.error(full_error)
            return {"status": "error", "message": full_error}
    except Exception as e:
        logger.error(f"Failed to start browser: {str(e)}")
        return {"status": "error", "message": f"Failed to start browser: {str(e)}"}

async def stop_browser(context=None):
    """Stop and clean up browser session"""
    # Get user ID for session tracking
    user_id = None
    if context and hasattr(context, "user") and context.user:
        user_id = context.user
    
    session_id = f"browser_{user_id}" if user_id else "browser_default"
    
    # Check if a session exists
    if session_id not in _browser_sessions:
        logger.info(f"No browser session {session_id} found to stop")
        return {"status": "ok", "message": "No browser running"}
    
    try:
        # Get session and quit driver
        client = _browser_sessions[session_id]
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, client.driver.quit)
        
        # Remove from sessions
        del _browser_sessions[session_id]
        
        logger.info(f"Stopped browser session {session_id}")
        return {"status": "ok", "message": "Browser stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop browser: {str(e)}")
        return {"status": "error", "message": f"Failed to stop browser: {str(e)}"}
