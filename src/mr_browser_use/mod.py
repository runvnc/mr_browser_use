"""
Browser use commands for MindRoot plugin
"""
from lib.providers.commands import command
import base64
import logging
from .browser_control import (
    check_browser_dependencies, 
    start_browser, 
    stop_browser, 
    get_browser_client,
    integrate_tab_handler
)
from lib.utils.debug import debug_box
import traceback
import json

logger = logging.getLogger(__name__)

import traceback
debug_box("----------------------------- mr_browser_use loaded ------------------------------------")

@command()
async def browser_check(context=None):
    """Check if browser dependencies are installed and available.
    
    Example:
    { "browser_check": {} }
    """
    result = await check_browser_dependencies()
    return result

@command()
async def browser_start(url=None, context=None):
    """Start the browser session.
    If a URL is provided, it will navigate to that URL.
    
    Parameters:
    url - String. Optional URL to navigate to after starting.
    
    Example:
    { "browser_start": {} }
    { "browser_start": {"url": "https://example.com"} }
    """
    # Start browser
    result = await start_browser(context)
    if result["status"] != "ok":
        return result
    
    # If URL provided, navigate to it
    # Get the browser client
    client = await get_browser_client(context)
    
    print(f"DEBUG [browser_start] Got client: {client}, tab_handler: {getattr(client, 'tab_handler', None)}")
    # Ensure tab handler is initialized before attempting navigation
    if hasattr(client, 'ensure_tab_handler'):
        print("DEBUG [browser_start] Client has ensure_tab_handler method, calling it")
        await client.ensure_tab_handler()
    elif hasattr(client, 'tab_handler') and client.tab_handler is None:
        # Fall back to manually initializing tab handler if needed
        print("DEBUG [browser_start] Client has tab_handler attribute but it's None, manually initializing")
        from .tab_handler import integrate_tab_handler
        await integrate_tab_handler(client)
    print(f"DEBUG [browser_start] After initialization, tab_handler: {getattr(client, 'tab_handler', None)}")
        
    # Now that browser is fully initialized, navigate to URL if provided
    if url:
        await client.navigate_to(url)
    
    try:
        return await browser_update_state(context)
    except Exception as e:
        logger.error(f"Screenshot error: {str(e)}")
        return str(e)
    

@command()
async def browser_stop(context=None):
    """Stop the browser session.
    
    Example:
    { "browser_stop": {} }
    """
    result = await stop_browser(context)
    return result

@command()
async def browser_screenshot(context=None):
    """Get a screenshot from the browser.
    This will insert the screenshot into the chat.
    
    Example:
    { "browser_screenshot": {} }
    """
    debug_box("top of screenshot")
    client = await get_browser_client(context)
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            # Insert the screenshot into the chat context
            message = await context.format_image_message(screenshot)
            return message
        else:
            return {"status": "error", "message": "Failed to get screenshot"}
    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"Screenshot command error: {str(e)} \n {trace}")
        return {"status": "error", "message": str(e) + "\n" + trace}

@command()
async def browser_navigate(url, context=None):
    """Navigate to a URL in the browser.
    
    Parameters:
    url - String. The URL to navigate to.
    
    Example:
    { "browser_navigate": {"url": "https://example.com"} }
    """
    if not url:
        return {"status": "error", "message": "URL is required"}
    
    client = await get_browser_client(context)
    result = await client.navigate_to(url)
    
    # Get a screenshot after navigation
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-navigation screenshot error: {str(e)}")
    
    return result

@command()
async def browser_update_state(context=None):
    """Update the browser state and get interactive elements.
    This will analyze the page, identify interactive elements, and return state data.
    
    Example:
    { "browser_update_state": {} }
    """
    client = await get_browser_client(context)
    state = await client.update_state()

    msgs = []
    try:
        scn_msg = await context.format_image_message(state["screenshot"])
        state.pop("screenshot")
        msgs.append(scn_msg)
        msgs.append({"type": "text", "text": json.dumps(state, indent=2)})
    except Exception as e:
        logger.error(f"Screenshot display error: {str(e)}")

    return msgs

@command()
async def browser_click_element(element_id, context=None):
    """Click on an interactive element by its ID.
    Use browser_update_state first to identify elements.
    
    Parameters:
    element_id - Integer. The ID of the element to click.
    
    Example:
    { "browser_click_element": {"element_id": 2} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    
    client = await get_browser_client(context)
    result = await client.click_element(element_id)
    
    # Get a screenshot after clicking
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-click screenshot error: {str(e)}")
    
    return result

@command()
async def browser_type_text(element_id, text, context=None):
    """Type text into an input element.
    
    Parameters:
    element_id - Integer. The ID of the element to type into.
    text - String. The text to type.
    
    Example:
    { "browser_type_text": {"element_id": 3, "text": "Hello world!"} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    if text is None:
        return {"status": "error", "message": "Text is required"}
    
    client = await get_browser_client(context)
    result = await client.type_text(element_id, text)
    
    # Get a screenshot after typing to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-type screenshot error: {str(e)}")
    
    return result

@command()
async def browser_hover(element_id, context=None):
    """Hover over an element.
    
    Parameters:
    element_id - Integer. The ID of the element to hover over.
    
    Example:
    { "browser_hover": {"element_id": 5} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    
    client = await get_browser_client(context)
    result = await client.hover(element_id)
    
    # Get a screenshot after hovering to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-hover screenshot error: {str(e)}")
    
    return result

@command()
async def browser_right_click(element_id, context=None):
    """Right-click on an element.
    
    Parameters:
    element_id - Integer. The ID of the element to right-click.
    
    Example:
    { "browser_right_click": {"element_id": 2} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    
    client = await get_browser_client(context)
    result = await client.right_click(element_id)
    
    # Get a screenshot after right-clicking to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-right-click screenshot error: {str(e)}")
    
    return result

@command()
async def browser_double_click(element_id, context=None):
    """Double-click on an element.
    
    Parameters:
    element_id - Integer. The ID of the element to double-click.
    
    Example:
    { "browser_double_click": {"element_id": 4} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    
    client = await get_browser_client(context)
    result = await client.double_click(element_id)
    
    # Get a screenshot after double-clicking to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-double-click screenshot error: {str(e)}")
    
    return result

@command()
async def browser_set_checkbox(element_id, checked=True, context=None):
    """Check or uncheck a checkbox.
    
    Parameters:
    element_id - Integer. The ID of the checkbox element.
    checked - Boolean. True to check, False to uncheck. Default is True.
    
    Example:
    { "browser_set_checkbox": {"element_id": 6, "checked": true} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    
    client = await get_browser_client(context)
    result = await client.set_checkbox(element_id, checked)
    
    # Get a screenshot after setting checkbox to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-checkbox screenshot error: {str(e)}")
    
    return result

@command()
async def browser_select_option(element_id, option_text=None, option_value=None, context=None):
    """Select an option from a dropdown/select element.
    
    Parameters:
    element_id - Integer. The ID of the select element.
    option_text - String. The visible text of the option to select.
    option_value - String. The value attribute of the option to select.
    
    Note: Provide either option_text OR option_value, not both.
    
    Example:
    { "browser_select_option": {"element_id": 7, "option_text": "California"} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    if option_text is None and option_value is None:
        return {"status": "error", "message": "Either option_text or option_value must be provided"}
    
    client = await get_browser_client(context)
    result = await client.select_option(element_id, option_text, option_value)
    
    # Get a screenshot after selecting option to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-select screenshot error: {str(e)}")
    
    return result

@command()
async def browser_drag_and_drop(source_id, target_id, context=None):
    """Drag an element and drop it onto another element.
    
    Parameters:
    source_id - Integer. The ID of the element to drag.
    target_id - Integer. The ID of the element to drop onto.
    
    Example:
    { "browser_drag_and_drop": {"source_id": 3, "target_id": 8} }
    """
    if source_id is None or target_id is None:
        return {"status": "error", "message": "Source and target element IDs are required"}
    
    client = await get_browser_client(context)
    result = await client.drag_and_drop(source_id, target_id)
    
    # Get a screenshot after drag and drop to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-drag-drop screenshot error: {str(e)}")
    
    return result

@command()
async def browser_press_key(key, context=None):
    """Press a keyboard key.
    
    Parameters:
    key - String. The key to press (e.g., "enter", "tab", "escape", "space").
    
    Example:
    { "browser_press_key": {"key": "enter"} }
    """
    if not key:
        return {"status": "error", "message": "Key parameter is required"}
    
    client = await get_browser_client(context)
    result = await client.press_key(key)
    
    # Get a screenshot after pressing key to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-keypress screenshot error: {str(e)}")
    
    return result

@command()
async def browser_key_combination(keys, context=None):
    """Press a combination of keys.
    
    Parameters:
    keys - String/List. Keys to press together (e.g., "ctrl+a", ["ctrl", "a"]).
    
    Example:
    { "browser_key_combination": {"keys": "ctrl+c"} }
    { "browser_key_combination": {"keys": ["ctrl", "shift", "i"]} }
    """
    if not keys:
        return {"status": "error", "message": "Keys parameter is required"}
    
    client = await get_browser_client(context)
    result = await client.key_combination(keys)
    
    # Get a screenshot after pressing keys to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-key-combination screenshot error: {str(e)}")
    
    return result

@command()
async def browser_scroll(direction="down", amount=300, context=None):
    """Scroll the page in the specified direction.
    
    Parameters:
    direction - String. Direction to scroll: "up", "down", "left", or "right". Default is "down".
    amount - Integer. The number of pixels to scroll. Default is 300.
    
    Example:
    { "browser_scroll": {"direction": "down", "amount": 500} }
    """
    client = await get_browser_client(context)
    result = await client.scroll(direction, amount)
    
    # Get a screenshot after scrolling to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-scroll screenshot error: {str(e)}")
    
    return result

@command()
async def browser_scroll_to_element(element_id, context=None):
    """Scroll to make an element visible.
    
    Parameters:
    element_id - Integer. The ID of the element to scroll to.
    
    Example:
    { "browser_scroll_to_element": {"element_id": 12} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    
    client = await get_browser_client(context)
    result = await client.scroll_to_element(element_id)
    
    # Get a screenshot after scrolling to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-scroll screenshot error: {str(e)}")
    
    return result

@command()
async def browser_go_back(context=None):
    """Navigate back in browser history.
    
    Example:
    { "browser_go_back": {} }
    """
    client = await get_browser_client(context)
    result = await client.go_back()
    
    # Get a screenshot after navigating back
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-back screenshot error: {str(e)}")
    
    return result

@command()
async def browser_go_forward(context=None):
    """Navigate forward in browser history.
    
    Example:
    { "browser_go_forward": {} }
    """
    client = await get_browser_client(context)
    result = await client.go_forward()
    
    # Get a screenshot after navigating forward
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-forward screenshot error: {str(e)}")
    
    return result

@command()
async def browser_refresh(context=None):
    """Refresh the current page.
    
    Example:
    { "browser_refresh": {} }
    """
    client = await get_browser_client(context)
    result = await client.refresh()
    
    # Get a screenshot after refreshing
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-refresh screenshot error: {str(e)}")
    
    return result

@command()
async def browser_get_text(element_id, context=None):
    """Get the text content of an element.
    
    Parameters:
    element_id - Integer. The ID of the element to get text from.
    
    Example:
    { "browser_get_text": {"element_id": 4} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    
    client = await get_browser_client(context)
    return await client.get_text(element_id)

@command()
async def browser_get_attribute(element_id, attribute_name, context=None):
    """Get the value of an element's attribute.
    
    Parameters:
    element_id - Integer. The ID of the element.
    attribute_name - String. The name of the attribute to get.
    
    Example:
    { "browser_get_attribute": {"element_id": 5, "attribute_name": "href"} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    if not attribute_name:
        return {"status": "error", "message": "Attribute name is required"}
    
    client = await get_browser_client(context)
    return await client.get_attribute(element_id, attribute_name)

@command()
async def browser_click_and_handle_new_tab(element_id, context=None):
    """Click on an element and automatically handle any new tab that opens.
    
    This command will click on the specified element, detect if a new tab opens,
    and automatically switch to that new tab if one is detected. The response will
    include information about whether a new tab was opened.
    
    Parameters:
    element_id - Integer. The ID of the element to click.
    
    Returns:
    A dictionary containing:
      - status: "ok" or "error"
      - new_tab_opened: Boolean indicating if a new tab was opened
      - message: Description of the result
      - handle: The window handle of the current tab
      - url: The URL of the current tab
      - title: The title of the current tab
      - original_handle: (if new_tab_opened is true) The handle of the original tab
    
    Example:
    { "browser_click_and_handle_new_tab": {"element_id": 2} }
    """
    if element_id is None:
        return {"status": "error", "message": "Element ID is required"}
    
    client = await get_browser_client(context)
    result = await client.click_element_and_handle_new_tab(element_id)
    
    # Get a screenshot after clicking to show the result
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-click screenshot error: {str(e)}")
    
    return result

@command()
async def browser_get_all_tabs(context=None):
    """Get information about all open tabs in the browser.
    
    Returns:
    A list of dictionaries, each containing:
      - handle: The window handle of the tab
      - url: The URL of the tab
      - title: The title of the tab
      - is_current: Boolean indicating if this is the currently active tab
    
    Example:
    { "browser_get_all_tabs": {} }
    """
    client = await get_browser_client(context)
    return await client.get_all_tabs()

@command()
async def browser_switch_to_tab(window_handle, context=None):
    """Switch to a specific tab by its window handle.
    
    Parameters:
    window_handle - String. The handle of the window/tab to switch to.
    
    Returns:
    A dictionary containing:
      - status: "ok" or "error"
      - handle: The window handle of the switched-to tab
      - url: The URL of the tab
      - title: The title of the tab
    
    Example:
    { "browser_switch_to_tab": {"window_handle": "CDwindow-123ABC..."} }
    """
    if not window_handle:
        return {"status": "error", "message": "Window handle is required"}
    
    client = await get_browser_client(context)
    result = await client.switch_to_tab(window_handle)
    
    # Get a screenshot after switching tabs
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-tab-switch screenshot error: {str(e)}")
    
    return result

@command()
async def browser_switch_to_newest_tab(context=None):
    """Switch to the most recently opened tab.
    
    Returns:
    A dictionary containing:
      - status: "ok", "error", or "info"
      - message: Description of the result (e.g., "No new tab found")
      - handle: The window handle of the current tab
      - url: The URL of the current tab
      - title: The title of the current tab
    
    Example:
    { "browser_switch_to_newest_tab": {} }
    """
    client = await get_browser_client(context)
    result = await client.switch_to_newest_tab()
    
    # Get a screenshot after switching tabs
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-tab-switch screenshot error: {str(e)}")
    
    return result

@command()
async def browser_switch_to_original_tab(context=None):
    """Switch back to the original tab (the first tab that was opened).
    
    Returns:
    A dictionary containing:
      - status: "ok" or "error"
      - handle: The window handle of the original tab
      - url: The URL of the original tab
      - title: The title of the original tab
    
    Example:
    { "browser_switch_to_original_tab": {} }
    """
    client = await get_browser_client(context)
    result = await client.switch_to_original_tab()
    
    # Get a screenshot after switching tabs
    try:
        screenshot = await client.get_screenshot()
        if screenshot:
            await context.format_image_message(screenshot)
    except Exception as e:
        logger.error(f"Post-tab-switch screenshot error: {str(e)}")
    
    return result

@command()
async def browser_close_current_tab(context=None):
    """Close the current tab and switch to another open tab.
    
    Returns:
    A dictionary containing:
      - status: "ok", "error", or "warn"
      - message: Description of the result
      - handle: (if a tab remains open) The window handle of the new current tab
      - url: (if a tab remains open) The URL of the new current tab
      - title: (if a tab remains open) The title of the new current tab
    
    Example:
    { "browser_close_current_tab": {} }
    """
    client = await get_browser_client(context)
    result = await client.close_current_tab()
    
    # Get a screenshot of the new current tab (if one remains)
    if result.get("status") == "ok":
        try:
            screenshot = await client.get_screenshot()
            if screenshot:
                await context.format_image_message(screenshot)
        except Exception as e:
            logger.error(f"Post-tab-close screenshot error: {str(e)}")
    
    return result
