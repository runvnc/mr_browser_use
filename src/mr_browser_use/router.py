"""
API routes for browser use plugin
"""
from fastapi import APIRouter, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from lib.templates import render
import logging
from .browser_control import (
    check_browser_dependencies,
    start_browser, 
    stop_browser, 
    get_browser_client
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/browser_use")
async def browser_use_page(request: Request):
    """Main browser use viewer page"""
    user = request.state.user.username if hasattr(request.state, 'user') else None
    html = await render('browser_view', {"user": user})
    return HTMLResponse(html)

@router.get("/browser_use/api/status")
async def browser_status(request: Request):
    """Get browser status"""
    # Check dependencies first
    deps_check = await check_browser_dependencies()
    if deps_check["status"] != "ok":
        return JSONResponse({"status": "dependency_error", "message": deps_check["message"]})
    
    # Try to get a client to see if browser is running
    try:
        # Pass request context
        context = request if hasattr(request, 'state') else None
        client = await get_browser_client(context)
        if client:
            # Check if it's still responsive by getting the current URL
            current_url = client.driver.current_url
            return JSONResponse({"status": "running", "url": current_url})
    except Exception as e:
        logger.debug(f"Browser status check error: {str(e)}")
        # Error accessing client means it's probably not running or crashed
        # We'll return not_running so the UI can offer to start it
        return JSONResponse({"status": "not_running"})
    
    # Default case if we get here
    return JSONResponse({"status": "not_running"})

@router.post("/browser_use/api/start")
async def browser_start(request: Request, url: str = None):
    """Start browser"""
    context = request if hasattr(request, 'state') else None
    result = await start_browser(context)
    
    # If URL was provided and browser started successfully, navigate to it
    if result["status"] == "ok" and url:
        try:
            client = await get_browser_client(context)
            nav_result = await client.navigate_to(url)
            result["navigation"] = nav_result
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            result["navigation_error"] = str(e)
    
    return JSONResponse(result)

@router.post("/browser_use/api/stop")
async def browser_stop(request: Request):
    """Stop browser"""
    context = request if hasattr(request, 'state') else None
    result = await stop_browser(context)
    return JSONResponse(result)

@router.post("/browser_use/api/navigate")
async def browser_navigate(request: Request, url: str = Body(...)):
    """Navigate to URL"""
    if not url:
        return JSONResponse({"status": "error", "message": "URL is required"})
    
    try:
        context = request if hasattr(request, 'state') else None
        client = await get_browser_client(context)
        result = await client.navigate_to(url)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Navigation error: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)})

@router.post("/browser_use/api/update_state")
async def browser_update_state(request: Request):
    """Update browser state and get interactive elements"""
    try:
        context = request if hasattr(request, 'state') else None
        client = await get_browser_client(context)
        state = await client.update_state()
        return JSONResponse(state)
    except Exception as e:
        logger.error(f"State update error: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)})

@router.post("/browser_use/api/click_element")
async def browser_click_element(request: Request, element_id: int = Body(...)):
    """Click on an element"""
    if element_id is None:
        return JSONResponse({"status": "error", "message": "Element ID is required"})
    
    try:
        context = request if hasattr(request, 'state') else None
        client = await get_browser_client(context)
        result = await client.click_element(element_id)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Click error: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)})
