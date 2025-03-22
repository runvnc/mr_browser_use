"""Tab handling utilities for the browser control module

Provides functions for detecting and managing browser tabs in Selenium sessions.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TabHandler:
    """Handles tab operations for browser sessions"""
    
    def __init__(self, driver):
        """Initialize with a WebDriver instance
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.original_window = driver.current_window_handle
        self.known_windows = {self.original_window}
    
    async def detect_new_tabs(self) -> Optional[str]:
        """Detect if any new tabs have been opened
        
        Returns:
            The handle of the new tab/window if found, None otherwise
        """
        current_windows = set(self.driver.window_handles)
        new_windows = current_windows - self.known_windows
        
        if new_windows:
            # Update known windows
            self.known_windows = current_windows
            # Return the first new window found
            return next(iter(new_windows))
        
        return None
    
    async def get_all_tabs(self) -> List[Dict[str, Any]]:
        """Get information about all open tabs
        
        Returns:
            List of dictionaries with tab information
        """
        result = []
        current_handle = self.driver.current_window_handle
        
        for handle in self.driver.window_handles:
            # Switch to the window to get its information
            self.driver.switch_to.window(handle)
            
            result.append({
                'handle': handle,
                'url': self.driver.current_url,
                'title': self.driver.title,
                'is_current': handle == current_handle
            })
        
        # Switch back to the original window
        self.driver.switch_to.window(current_handle)
        
        return result
    
    async def switch_to_tab(self, window_handle: str) -> Dict[str, Any]:
        """Switch to specified tab/window
        
        Args:
            window_handle: The handle of the window to switch to
            
        Returns:
            Information about the tab switched to
        """
        try:
            self.driver.switch_to.window(window_handle)
            return {
                'status': 'ok',
                'handle': window_handle,
                'url': self.driver.current_url,
                'title': self.driver.title
            }
        except Exception as e:
            logger.error(f"Error switching to tab: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def switch_to_newest_tab(self) -> Dict[str, Any]:
        """Switch to the most recently opened tab
        
        Returns:
            Information about the tab switched to
        """
        newest_tab = None
        
        # Find the newest tab by comparing with known windows
        current_windows = self.driver.window_handles
        if len(current_windows) > len(self.known_windows):
            for handle in reversed(current_windows):  # Newer tabs are often at the end
                if handle not in self.known_windows:
                    newest_tab = handle
                    break
        
        # Update known windows
        self.known_windows = set(current_windows)
        
        if newest_tab:
            return await self.switch_to_tab(newest_tab)
        else:
            # No new tab found, return current
            return {
                'status': 'info',
                'message': 'No new tab found',
                'handle': self.driver.current_window_handle,
                'url': self.driver.current_url,
                'title': self.driver.title
            }
    
    async def switch_to_original_tab(self) -> Dict[str, Any]:
        """Switch back to the original tab
        
        Returns:
            Information about the original tab
        """
        return await self.switch_to_tab(self.original_window)
    
    async def close_current_tab(self) -> Dict[str, Any]:
        """Close the current tab and switch to another open tab
        
        Returns:
            Information about the new current tab
        """
        try:
            current_handle = self.driver.current_window_handle
            self.driver.close()
            
            # Update known windows
            self.known_windows.discard(current_handle)
            
            # Switch to another window if any remain
            remaining_windows = self.driver.window_handles
            if remaining_windows:
                new_handle = remaining_windows[0]
                return await self.switch_to_tab(new_handle)
            else:
                return {
                    'status': 'warn',
                    'message': 'All tabs closed'
                }
        except Exception as e:
            logger.error(f"Error closing tab: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def click_and_switch_if_new_tab(self, element_id: int) -> Dict[str, Any]:
        """Click an element and switch to new tab if one opens
        
        Args:
            element_id: ID of the element to click
            
        Returns:
            Status and information about the operation
        """
        try:
            # Store window handles before click
            handles_before = set(self.driver.window_handles)
            
            # Get the element and click it
            script = f"""
            return window.browserUseElements[{element_id}];
            """
            element = self.driver.execute_script(script)
            if not element:
                return {
                    'status': 'error',
                    'message': f"Element {element_id} not found"
                }
            
            # Click the element
            element.click()
            
            # Wait a moment for any new tab to open
            import time
            time.sleep(0.5)
            
            # Check for new tabs
            handles_after = set(self.driver.window_handles)
            new_tabs = handles_after - handles_before
            
            if new_tabs:
                # Switch to the new tab
                new_tab = next(iter(new_tabs))
                self.known_windows = handles_after
                result = await self.switch_to_tab(new_tab)
                
                # Add explicit indication that a new tab was opened
                if result['status'] == 'ok':
                    result['new_tab_opened'] = True
                    result['original_handle'] = self.original_window
                    result['message'] = f"Clicked element and switched to new tab: {result['title']}"
                
                return result
            else:
                # No new tab opened, return status
                return {
                    'status': 'ok',
                    'new_tab_opened': False,
                    'message': 'Element clicked, no new tab opened',
                    'handle': self.driver.current_window_handle,
                    'url': self.driver.current_url,
                    'title': self.driver.title
                }
        except Exception as e:
            logger.error(f"Error in click and switch: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

# Factory function to create TabHandler instance
async def get_tab_handler(browser_client):
    """Create a TabHandler for a browser client
    
    Args:
        browser_client: BrowserClient instance
        
    Returns:
        TabHandler instance
    """
    print(f"DEBUG [get_tab_handler] Called with browser_client: {browser_client}")
    if not browser_client or not hasattr(browser_client, 'driver'):
        logger.error("Invalid browser client provided")
        print(f"DEBUG [get_tab_handler] Invalid browser client: {browser_client}")
        return None
    
    print(f"DEBUG [get_tab_handler] Creating new TabHandler with driver: {browser_client.driver}")
    return TabHandler(browser_client.driver)

# Integration functions to add to BrowserClient
async def integrate_tab_handler(browser_client):
    """Add tab handler capabilities to browser client
    
    Args:
        browser_client: BrowserClient instance to enhance
        
    Returns:
        Enhanced browser client
    """
    print(f"DEBUG [integrate_tab_handler] Called with browser_client: {browser_client}")
    if not hasattr(browser_client, 'tab_handler'):
        print("DEBUG [integrate_tab_handler] Client has no tab_handler attribute, creating one")
        browser_client.tab_handler = await get_tab_handler(browser_client)
    
    # Add method references to the browser client
    if not hasattr(browser_client, 'detect_new_tabs'):
        print("DEBUG [integrate_tab_handler] Adding tab handler methods to browser client")
        browser_client.detect_new_tabs = browser_client.tab_handler.detect_new_tabs
        browser_client.get_all_tabs = browser_client.tab_handler.get_all_tabs
        browser_client.switch_to_tab = browser_client.tab_handler.switch_to_tab
        browser_client.switch_to_newest_tab = browser_client.tab_handler.switch_to_newest_tab
        browser_client.switch_to_original_tab = browser_client.tab_handler.switch_to_original_tab
        browser_client.close_current_tab = browser_client.tab_handler.close_current_tab
        browser_client.click_and_switch_if_new_tab = browser_client.tab_handler.click_and_switch_if_new_tab
    else:
        print("DEBUG [integrate_tab_handler] Client already has tab handler methods attached")
    
    return browser_client