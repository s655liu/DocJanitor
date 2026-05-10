import * as vscode from 'vscode';

export class SidebarProvider implements vscode.WebviewViewProvider {
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
    }

    public update(status: any) {
        if (this._view) {
            this._view.webview.postMessage({ type: 'update', data: status });
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Janitor Status</title>
                <style>
                    body { font-family: sans-serif; padding: 10px; color: var(--vscode-foreground); }
                    .card { border: 1px solid var(--vscode-widget-border); padding: 10px; border-radius: 4px; margin-bottom: 10px; }
                    .tier-minor { color: #4fc1ff; }
                    .tier-major { color: #f44336; font-weight: bold; }
                    .model { font-size: 0.9em; opacity: 0.8; }
                </style>
            </head>
            <body>
                <h3>Agent Status</h3>
                <div id="status-container">
                    <p>Waiting for agent...</p>
                </div>
                <script>
                    const vscode = acquireVsCodeApi();
                    window.addEventListener('message', event => {
                        const message = event.data;
                        if (message.type === 'update') {
                            const container = document.getElementById('status-container');
                            const status = message.data;
                            container.innerHTML = \`
                                <div class="card">
                                    <div class="tier-\${status.tier.toLowerCase()}">\${status.tier} Change</div>
                                    <div class="model">Model: \${status.model}</div>
                                    <p>\${status.summary}</p>
                                    <small>\${new Date().toLocaleTimeString()}</small>
                                </div>
                            \`;
                        }
                    });
                </script>
            </body>
            </html>
        `;
    }
}
