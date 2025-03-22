import { BaseEl } from '/chat/static/js/base.js';
import { html, css } from '/chat/static/js/lit-core.min.js';

class BrowserViewer extends BaseEl {
  static properties = {
    refreshRate: { type: Number },
    browserStatus: { type: String },
    currentUrl: { type: String },
    elements: { type: Array },
    currentElement: { type: Object },
    screenshot: { type: String },
    isFullscreen: { type: Boolean }
  };

  static styles = css`
    :host {
      display: block;
      background: var(--component-bg, var(--background-color));
      color: var(--component-text, var(--text-color));
      border-radius: 8px;
      overflow: hidden;
      margin: 1rem 0;
    }
    
    .container {
      display: flex;
      flex-direction: column;
      height: 100%;
    }
    
    .toolbar {
      display: flex;
      justify-content: space-between;
      padding: 0.5rem;
      background: rgba(0,0,0,0.2);
    }
    
    .url-bar {
      display: flex;
      padding: 0.25rem;
      background: rgba(0,0,0,0.1);
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .url-bar input {
      flex: 1;
      margin-right: 0.5rem;
      padding: 0.25rem 0.5rem;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 4px;
      color: var(--component-text, var(--text-color));
    }
    
    .url-bar button,
    .toolbar button {
      margin-left: 0.5rem;
      padding: 0.25rem 0.5rem;
      background: var(--link-color);
      border: none;
      border-radius: 4px;
      color: white;
      cursor: pointer;
    }
    
    .toolbar button.stop {
      background: #e74c3c;
    }
    
    .toolbar button.refresh {
      background: #2ecc71;
    }
    
    .screen {
      flex: 1;
      min-height: 400px;
      border: 1px solid rgba(255,255,255,0.1);
      background: #000;
      position: relative;
      overflow: auto;
    }
    
    .screenshot-container {
      position: relative;
      display: inline-block;
    }
    
    .screenshot-container img {
      max-width: 100%;
      height: auto;
      display: block;
    }
    
    .element-overlay {
      position: absolute;
      pointer-events: all;
      cursor: pointer;
      box-sizing: border-box;
      border: 2px solid transparent;
      background-color: rgba(0, 128, 255, 0.1);
      transition: border-color 0.2s, background-color 0.2s;
    }
    
    .element-overlay:hover {
      border-color: rgba(0, 128, 255, 0.8);
      background-color: rgba(0, 128, 255, 0.2);
    }
    
    .element-overlay .element-id {
      position: absolute;
      top: -16px;
      left: 0;
      background: rgba(0, 128, 255, 0.8);
      color: white;
      font-size: 10px;
      padding: 1px 4px;
      border-radius: 2px;
    }
    
    .status {
      color: #aaa;
      padding: 0.5rem;
      font-size: 0.8rem;
    }
    
    .fullscreen {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 1000;
      border-radius: 0;
    }
    
    .fullscreen .screen {
      min-height: calc(100vh - 90px);
    }
    
    .elements-list {
      max-height: 200px;
      overflow-y: auto;
      background: rgba(0,0,0,0.2);
      border-top: 1px solid rgba(255,255,255,0.1);
      padding: 0.5rem;
    }
    
    .element-item {
      display: flex;
      padding: 0.25rem;
      border-bottom: 1px solid rgba(255,255,255,0.05);
      cursor: pointer;
    }
    
    .element-item:hover {
      background: rgba(255,255,255,0.05);
    }
    
    .element-item .element-id {
      background: var(--link-color);
      color: white;
      padding: 0 4px;
      border-radius: 2px;
      margin-right: 0.5rem;
      font-size: 12px;
    }
    
    .element-item .element-tag {
      font-weight: bold;
      margin-right: 0.5rem;
      color: #e74c3c;
    }
    
    .element-item .element-text {
      color: #aaa;
      font-size: 0.9em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
    }
    
    .element-details {
      background: rgba(0,0,0,0.3);
      padding: 0.5rem;
      margin-top: 0.5rem;
      border-radius: 4px;
      display: none;
    }
    
    .element-details.visible {
      display: block;
    }
    
    .element-details h4 {
      margin: 0.5rem 0;
      color: #3498db;
    }
    
    .element-details code {
      display: block;
      background: rgba(0,0,0,0.2);
      padding: 0.25rem;
      margin: 0.25rem 0;
      border-radius: 2px;
      font-family: monospace;
      font-size: 12px;
      white-space: pre-wrap;
      word-break: break-all;
    }
  `;

  constructor() {
    super();
    this.refreshRate = 2000; // ms
    this.browserStatus = 'unknown';
    this.currentUrl = '';
    this.elements = [];
    this.currentElement = null;
    this.screenshot = null;
    this.isFullscreen = false;
    this.interval = null;
    
    // Bind methods
    this.handleNavigate = this.handleNavigate.bind(this);
    this.startBrowser = this.startBrowser.bind(this);
    this.stopBrowser = this.stopBrowser.bind(this);
    this.updateState = this.updateState.bind(this);
    this.handleElementClick = this.handleElementClick.bind(this);
    this.toggleFullscreen = this.toggleFullscreen.bind(this);
  }
  
  connectedCallback() {
    super.connectedCallback();
    this.checkBrowserStatus();
    this.interval = setInterval(() => this.checkBrowserStatus(), this.refreshRate);
  }
  
  disconnectedCallback() {
    super.disconnectedCallback();
    if (this.interval) {
      clearInterval(this.interval);
    }
  }
  
  async checkBrowserStatus() {
    try {
      const response = await fetch('/browser_use/api/status');
      const data = await response.json();
      this.browserStatus = data.status;
      
      if (data.status === 'running' && data.url) {
        this.currentUrl = data.url;
        // If browser is running, update the state
        this.updateState();
      }
    } catch (error) {
      this.browserStatus = 'error';
      console.error('Failed to check browser status:', error);
    }
  }
  
  async startBrowser() {
    try {
      this.browserStatus = 'starting';
      // Get URL from input if available
      const urlInput = this.shadowRoot.querySelector('.url-input');
      const url = urlInput && urlInput.value ? urlInput.value : null;
      
      // Start browser with optional URL
      const response = await fetch('/browser_use/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      
      const data = await response.json();
      if (data.status === 'ok') {
        this.browserStatus = 'running';
        this.updateState();
      } else {
        this.browserStatus = 'error';
      }
    } catch (error) {
      this.browserStatus = 'error';
      console.error('Failed to start browser:', error);
    }
  }
  
  async stopBrowser() {
    try {
      this.browserStatus = 'stopping';
      const response = await fetch('/browser_use/api/stop', {
        method: 'POST'
      });
      
      const data = await response.json();
      if (data.status === 'ok') {
        this.browserStatus = 'not_running';
        this.elements = [];
        this.screenshot = null;
      } else {
        this.browserStatus = 'error';
      }
    } catch (error) {
      this.browserStatus = 'error';
      console.error('Failed to stop browser:', error);
    }
  }
  
  async updateState() {
    if (this.browserStatus !== 'running') return;
    
    try {
      const response = await fetch('/browser_use/api/update_state', {
        method: 'POST'
      });
      
      const data = await response.json();
      if (data.status === 'ok') {
        this.elements = data.elements || [];
        this.screenshot = data.screenshot;
        this.currentUrl = data.url;
      }
    } catch (error) {
      console.error('Failed to update state:', error);
    }
  }
  
  async handleNavigate(event) {
    event.preventDefault();
    const urlInput = this.shadowRoot.querySelector('.url-input');
    if (!urlInput || !urlInput.value) return;
    
    this.currentUrl = urlInput.value;
    
    try {
      const response = await fetch('/browser_use/api/navigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: this.currentUrl })
      });
      
      const data = await response.json();
      if (data.status === 'ok') {
        // Update state after navigation
        setTimeout(() => this.updateState(), 1000);
      }
    } catch (error) {
      console.error('Navigation error:', error);
    }
  }
  
  async handleElementClick(elementId) {
    try {
      const response = await fetch('/browser_use/api/click_element', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ element_id: elementId })
      });
      
      const data = await response.json();
      if (data.status === 'ok') {
        // Update state after clicking
        setTimeout(() => this.updateState(), 1000);
      }
    } catch (error) {
      console.error('Click error:', error);
    }
  }
  
  toggleFullscreen() {
    this.isFullscreen = !this.isFullscreen;
  }
  
  showElementDetails(element) {
    this.currentElement = element;
    this.requestUpdate();
  }
  
  _render() {
    return html`
      <div class="container ${this.isFullscreen ? 'fullscreen' : ''}">
        <div class="toolbar">
          <div>
            <span>Browser Status: ${this.browserStatus}</span>
          </div>
          <div>
            ${this.browserStatus !== 'running' ? 
              html`<button @click=${this.startBrowser}>Start Browser</button>` : 
              html`<button class="stop" @click=${this.stopBrowser}>Stop Browser</button>`
            }
            ${this.browserStatus === 'running' ? 
              html`<button class="refresh" @click=${this.updateState}>Refresh State</button>` : 
              ''
            }
            <button @click=${this.toggleFullscreen}>
              ${this.isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            </button>
          </div>
        </div>
        
        <div class="url-bar">
          <input type="text" class="url-input" placeholder="Enter URL" 
                 .value=${this.currentUrl} 
                 ?disabled=${this.browserStatus !== 'running'} />
          <button @click=${this.handleNavigate} ?disabled=${this.browserStatus !== 'running'}>Navigate</button>
        </div>
        
        <div class="screen">
          ${this.browserStatus === 'running' && this.screenshot ?
            html`<div class="screenshot-container">
              <img src="data:image/png;base64,${this.screenshot}" alt="Browser screenshot" />
              ${this.elements.map(el => 
                html`<div class="element-overlay" 
                      style="left: ${el.rect.left}px; top: ${el.rect.top}px; 
                             width: ${el.rect.width}px; height: ${el.rect.height}px;"
                      @click=${() => this.handleElementClick(el.id)}>
                  <span class="element-id">${el.id}</span>
                </div>`
              )}
            </div>` :
            html`<div class="status">
              ${this.browserStatus === 'starting' ? 'Starting browser...' :
                this.browserStatus === 'stopping' ? 'Stopping browser...' :
                this.browserStatus === 'not_running' ? 'Browser not running. Click Start to launch.' :
                'Browser state unknown. Try refreshing or starting the browser.'}
            </div>`
          }
        </div>
        
        ${this.elements.length > 0 ? 
          html`<div class="elements-list">
            <h3>Interactive Elements (${this.elements.length})</h3>
            ${this.elements.map(el => 
              html`<div class="element-item" @click=${() => this.showElementDetails(el)}>
                <span class="element-id">${el.id}</span>
                <span class="element-tag">${el.tagName}</span>
                <span class="element-text">${el.text || '[no text]'}</span>
              </div>`
            )}
            
            ${this.currentElement ? 
              html`<div class="element-details visible">
                <h4>${this.currentElement.tagName} Element (ID: ${this.currentElement.id})</h4>
                <p>Text: ${this.currentElement.text || '[no text]'}</p>
                
                <h4>Attributes:</h4>
                <code>${JSON.stringify(this.currentElement.attributes, null, 2)}</code>
                
                <h4>XPath:</h4>
                <code>${this.currentElement.xpath}</code>
                
                <button @click=${() => this.handleElementClick(this.currentElement.id)}>Click This Element</button>
              </div>` : ''
            }
          </div>` : ''
        }
      </div>
    `;
  }
}

customElements.define('browser-viewer', BrowserViewer);

// Register command handlers
window.registerCommandHandler('browser_start', (data) => {
  if (data.event === 'result') {
    return html`<div>Browser started. Use the browser viewer to interact with it.</div>`;
  }
  return null;
});

window.registerCommandHandler('browser_screenshot', (data) => {
  // Screenshot is added to chat via format_image_message
  // No need to return anything here
  return null;
});

window.registerCommandHandler('browser_update_state', (data) => {
  if (data.event === 'result') {
    const elements = data.args.elements || [];
    return html`<div>
      <p>Found ${elements.length} interactive elements on the page.</p>
      <p>Current URL: ${data.args.url}</p>
    </div>`;
  }
  return null;
});
