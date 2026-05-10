import * as vscode from 'vscode';

export class SidebarProvider implements vscode.WebviewViewProvider {
    private _view?: vscode.WebviewView;
    private _lastStatus: any = null;

    constructor(private readonly _extensionUri: vscode.Uri) { }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // If we already have a status, send it immediately
        if (this._lastStatus) {
            this.update(this._lastStatus);
        }
    }

    public update(status: any) {
        this._lastStatus = status;
        if (this._view) {
            this._view.webview.postMessage({ type: 'update', data: status });
        }
    }

    private _getHtmlForWebview(_webview: vscode.Webview) {
        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: var(--vscode-font-family); padding: 15px; color: var(--vscode-foreground); background: var(--vscode-sideBar-background); }
                    .card { 
                        background: var(--vscode-editor-background); 
                        border: 1px solid var(--vscode-widget-border); 
                        padding: 12px; 
                        border-radius: 8px; 
                        margin-bottom: 12px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        border-left: 4px solid #4fc1ff;
                    }
                    .tier-major .card { border-left-color: #f44336; }
                    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
                    .tier-tag { font-size: 0.7em; text-transform: uppercase; font-weight: bold; padding: 2px 6px; border-radius: 4px; background: rgba(79, 193, 255, 0.1); color: #4fc1ff; }
                    .tier-major .tier-tag { background: rgba(244, 67, 54, 0.1); color: #f44336; }
                    .model { font-size: 0.8em; color: var(--vscode-descriptionForeground); margin-bottom: 10px; }
                    .summary { font-size: 0.95em; line-height: 1.4; margin: 10px 0; }
                    .timestamp { font-size: 0.75em; opacity: 0.5; text-align: right; }
                    .pulse { width: 8px; height: 8px; background: #4fc1ff; border-radius: 50%; display: inline-block; margin-right: 6px; box-shadow: 0 0 0 rgba(79, 193, 255, 0.4); animation: pulse 2s infinite; }
                    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(79, 193, 255, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(79, 193, 255, 0); } 100% { box-shadow: 0 0 0 0 rgba(79, 193, 255, 0); } }
                </style>
            </head>
            <body>
                <div id="status-container">
                    <div class="card">
                        <div class="header"><span class="pulse"></span> <b>Agent Active</b></div>
                        <p>Waiting for first change event...</p>
                    </div>
                </div>
                <script>
                    const vscode = acquireVsCodeApi();
                    window.addEventListener('message', event => {
                        const message = event.data;
                        console.log('Received message:', JSON.stringify(message));
                        if (message.type === 'update') {
                            const status = message.data;
                            console.log('Status payload:', JSON.stringify(status));
                            const container = document.getElementById('status-container');
                            
                            const isUpdating = status.event === 'updating';
                            const cardClass = status.tier === 'major' ? 'tier-major' : '';
                            const statusTag = isUpdating ? 'Processing' : \`\${status.tier} Change\`;
                            const pulseHtml = isUpdating ? '<span class="pulse"></span>' : '';

                            container.innerHTML = \`
                                <div class="\${cardClass}">
                                    <div class="card">
                                        <div class="header">
                                            \${pulseHtml}
                                            <span class="tier-tag">\${statusTag}</span>
                                        </div>
                                        <div class="model">Model: \${status.model}</div>
                                        <div class="summary">\${status.summary}</div>
                                        <pre id="diff-block" style="background:var(--vscode-textBlockQuote-background);padding:8px;border-radius:4px;overflow-x:auto;font-size:0.8em;white-space:pre-wrap;margin-top:8px;display:none;"></pre>
                                        <div class="timestamp">\${new Date().toLocaleTimeString()}</div>
                                    </div>
                                </div>
                            \`;
                            
                            if (status.diff && !isUpdating) {
                                const diffEl = document.getElementById('diff-block');
                                diffEl.textContent = status.diff;
                                diffEl.style.display = 'block';
                            }
                        }
                    });
                </script>
            </body>
            </html>
        `;
    }
}
