/**
 * DOM Analyzer for Browser Use Plugin
 * 
 * Enhanced version with better event listener detection
 * This script identifies interactive elements on the page and optionally highlights them
 */

function findInteractiveElements(options = {}) {
  const { 
    highlightElements = true, 
    focusElement = -1,
    viewportExpansion = 0 
  } = options;
  
  // Remove any existing highlights
  removeHighlights();
  
  // Element storage for access from Python
  window.browserUseElements = window.browserUseElements || {};
  window.removeHighlights = removeHighlights;
  // Highlighted elements tracking
  const highlightedElements = [];
  let highlightIndex = 0;
  
  // Main interactive element selectors
  const interactiveSelectors = [
    // Standard interactive elements
    'a', 'button', 'input', 'select', 'textarea',
    '[role="button"]', '[tabindex="0"]', '[onclick]',
    'summary', 'details', 'label', 'option',
    'iframe', 'video', 'audio', 'menu', 'menuitem',
    '[contenteditable="true"]',
    
    // Add SVG-specific selectors
    'svg path', 'svg rect', 'svg polygon', 'svg g', 
    'svg circle', 'svg ellipse',
    
    // Add map-specific selectors
    'map area', '[usemap]'
  ];
  
  // Find all potentially interactive elements
  const elements = document.querySelectorAll(interactiveSelectors.join(','));
  
  // Process each element
  const result = [];
  
  // Process and store interactive elements
  function processElements(elementList) {
    Array.from(elementList).forEach(element => {
      // Skip invisible elements
      if (!isElementVisible(element)) {
        return;
      }
      
      // Get element details
      const rect = element.getBoundingClientRect();
      
      // Skip elements outside the expanded viewport
      if (!isInExpandedViewport(rect, viewportExpansion)) {
        return;
      }
      
      // Generate a unique identifier for this element
      const id = highlightIndex++;
      
      // Get basic information about the element
      const elementData = {
        id: id,
        tagName: element.tagName.toLowerCase(),
        text: element.textContent.trim().substring(0, 200),
        attributes: getKeyAttributes(element)
        //xpath: getElementXPath(element)
        /* rect: {
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height
        }*/ 
      };
      
      // Store element for later use (click operations, etc.)
      window.browserUseElements[id] = element;
      
      // Add to result array
      result.push(elementData);
      
      // Highlight the element if requested
      if (highlightElements && (focusElement === -1 || focusElement === id)) {
        highlightElement(element, id);
        highlightedElements.push(element);
      }
    });
  }
  
  // Process standard interactive elements
  processElements(elements);
  
  // Find and process elements with event listeners or pointer cursor
  const elementsWithEvents = findElementsWithEventListeners();
  processElements(elementsWithEvents);

  // Return the elements and page info
  return {
    elements: result,
    url: document.location.href,
    title: document.title
  };
}

/**
 * Find elements with event listeners or cursor:pointer
 */
function findElementsWithEventListeners() {
  const results = new Set();
  
  // Check all elements on the page
  const allElements = document.querySelectorAll('*');
  
  Array.from(allElements).forEach(element => {
    // Skip elements we already know are standard interactive elements
    if (element.tagName === 'A' || element.tagName === 'BUTTON' || 
        element.tagName === 'INPUT' || element.tagName === 'SELECT') {
      return;
    }
    
    // Check for event handlers directly on the element
    const hasClickHandler =
      element.onclick !== null ||
      element.getAttribute("onclick") !== null ||
      element.hasAttribute("ng-click") ||
      element.hasAttribute("@click") ||
      element.hasAttribute("v-on:click");
    
    if (hasClickHandler) {
      results.add(element);
      return;
    }
    
    // Check computed styles for cursor: pointer (strong indicator of clickable elements)
    const style = window.getComputedStyle(element);
    if (style.cursor === 'pointer') {
      results.add(element);
      return;
    }
    
    // Check for event listeners using our best approach
    const listeners = getEventListeners(element);
    const hasClickListeners =
      listeners &&
      (listeners.click?.length > 0 ||
       listeners.mousedown?.length > 0 ||
       listeners.mouseup?.length > 0 ||
       listeners.touchstart?.length > 0 ||
       listeners.touchend?.length > 0);
    
    if (hasClickListeners) {
      results.add(element);
    }
  });
  
  return Array.from(results);
}

/**
 * Helper function to safely get event listeners
 */
function getEventListeners(el) {
  try {
    // Try the official API if available (Chrome DevTools)
    if (window.getEventListeners) {
      return window.getEventListeners(el) || {};
    }
    
    // Fallback: check for on* properties
    const listeners = {};
    const eventTypes = [
      "click", "mousedown", "mouseup", "touchstart", "touchend",
      "mouseover", "mouseout", "keydown", "keyup", "focus", "blur"
    ];
    
    for (const type of eventTypes) {
      const handler = el[`on${type}`];
      if (handler) {
        listeners[type] = [{ listener: handler, useCapture: false }];
      }
    }
    
    return listeners;
  } catch (e) {
    return {};
  }
}

/**
 * Check if an element is visible and interactable
 */
function isElementVisible(element) {
  // Get computed style
  const style = window.getComputedStyle(element);
  
  // Basic checks for visibility
  if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
    return false;
  }
  
  // Check if element has a size
  const rect = element.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) {
    return false;
  }
  
  return true;
}

/**
 * Check if an element is within the expanded viewport
 */
function isInExpandedViewport(rect, expansion) {
  // If expansion is -1, include all elements
  if (expansion === -1) {
    return true;
  }
  
  // Check if element is within the expanded viewport
  return !(rect.bottom < -expansion ||
           rect.top > window.innerHeight + expansion ||
           rect.right < -expansion ||
           rect.left > window.innerWidth + expansion);
}

/**
 * Get key attributes for element identification
 */
function getKeyAttributes(element) {
  const attributes = {};
  
  // Interesting attributes to capture
  const attributeNames = [
    'id', 'name', 'value', 'type', 'href', 'src', 
    'alt', 'placeholder', 'aria-label', 'title', 'role',
    'class', 'data-id', 'data-name', 'data-value'
  ];
  
  // Collect attributes
  attributeNames.forEach(name => {
    if (element.hasAttribute(name)) {
      attributes[name] = element.getAttribute(name);
      if (name === 'href' || name === 'src' || name == 'data-value') {
        attributes[name] = attributes[name].substring(0, 200);
      }
    }
  });
  
  return attributes;
}

/**
 * Get XPath for an element
 */
function getElementXPath(element) {
  const paths = [];
  for (let node = element; 
       node && node.nodeType === Node.ELEMENT_NODE; 
       node = node.parentNode) {
    let index = 0;
    for (let sibling = node.previousSibling; 
         sibling; 
         sibling = sibling.previousSibling) {
      if (sibling.nodeType === Node.ELEMENT_NODE && 
          sibling.tagName === node.tagName) {
        index++;
      }
    }
    const tagName = node.tagName.toLowerCase();
    const pathIndex = index ? `[${index + 1}]` : '';
    paths.unshift(`${tagName}${pathIndex}`);
  }
  return paths.length ? `/${paths.join('/')}` : '';
}

/**
 * Highlight an element on the page
 */
function highlightElement(element, id) {
  // Create container if it doesn't exist
  let container = document.getElementById('browser-use-highlights');
  if (!container) {
    container = document.createElement('div');
    container.id = 'browser-use-highlights';
    container.style.position = 'fixed';
    container.style.pointerEvents = 'none';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
  }
  
  // Get element position
  const rect = element.getBoundingClientRect();
  
  // Generate color based on ID
  const colors = [
    '#FF0000', '#00FF00', '#0000FF', '#FFFF00', 
    '#FF00FF', '#00FFFF', '#FFA500', '#800080'
  ];
  const colorIndex = id % colors.length;
  const baseColor = colors[colorIndex];
  
  // Create highlight overlay
  const overlay = document.createElement('div');
  overlay.className = 'browser-use-highlight';
  overlay.style.position = 'fixed';
  overlay.style.border = `2px solid ${baseColor}`;
  overlay.style.backgroundColor = `${baseColor}1A`; // 10% opacity
  overlay.style.top = `${rect.top}px`;
  overlay.style.left = `${rect.left}px`;
  overlay.style.width = `${rect.width}px`;
  overlay.style.height = `${rect.height}px`;
  overlay.style.pointerEvents = 'none';
  
  // Add ID label
  const label = document.createElement('div');
  label.className = 'browser-use-highlight-label';
  label.style.position = 'fixed';
  label.style.background = baseColor;
  label.style.color = 'white';
  label.style.padding = '2px 4px';
  label.style.borderRadius = '2px';
  label.style.fontSize = '12px';
  label.style.top = `${rect.top - 14}px`;
  label.style.left = `${rect.left}px`;
  label.textContent = id;
  
  // Add to container
  container.appendChild(overlay);
  container.appendChild(label);
}

/**
 * Remove all highlights
 */
function removeHighlights() {
  const container = document.getElementById('browser-use-highlights');
  if (container) {
    container.remove();
  }
}
