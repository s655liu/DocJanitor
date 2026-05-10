import * as vscode from 'vscode';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';

export class AgentBridge {
    private agentProcess: ChildProcess | null = null;
    private statusListeners: ((status: any) => void)[] = [];
    private stdoutBuffer: string = '';

    constructor(
        private context: vscode.ExtensionContext,
        private outputChannel: vscode.OutputChannel
    ) {}

    public async start() {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        const agentPath = path.join(this.context.extensionPath, '..', 'agent', 'main.py');
        
        // 1. Get path from VS Code Settings (User or Workspace)
        // 2. Default to 'python' if not set
        const config = vscode.workspace.getConfiguration('janitor');
        const pythonPath = config.get<string>('pythonPath') || 'python';

        this.outputChannel.appendLine(`[Bridge] Agent script: ${agentPath}`);
        this.outputChannel.appendLine(`[Bridge] Working dir: ${workspaceFolder}`);
        this.outputChannel.appendLine(`[Bridge] Using Python: ${pythonPath}`);
        this.outputChannel.show();

        this.agentProcess = spawn(pythonPath, [agentPath], {
            cwd: workspaceFolder
        });

        this.agentProcess.stdout?.on('data', (data) => {
            this.stdoutBuffer += data.toString();
            const lines = this.stdoutBuffer.split('\n');
            this.stdoutBuffer = lines.pop() || '';
            
            for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.startsWith('{')) {
                    try {
                        const payload = JSON.parse(trimmed);
                        if (payload.event) {
                            this.notifyListeners(payload);
                            if (payload.event === 'updated') {
                                vscode.window.showInformationMessage(`Janitor: ${payload.summary}`);
                            }
                        }
                    } catch (e) {
                        this.outputChannel.appendLine(`[Parse Error]: ${trimmed}`);
                    }
                }
            }
        });

        this.agentProcess.stderr?.on('data', (data) => {
            const err = data.toString();
            this.outputChannel.appendLine(`[Agent Error]: ${err}`);
            if (err.includes("ModuleNotFoundError")) {
                vscode.window.showErrorMessage(`Janitor: Missing dependencies. Please run 'pip install -r requirements.txt' in the ${pythonPath} environment.`);
            }
        });

        this.agentProcess.on('error', (err) => {
            this.outputChannel.appendLine(`[Bridge Error]: Failed to start agent: ${err.message}`);
            vscode.window.showErrorMessage(`Janitor: Could not find Python at '${pythonPath}'. Please check your 'janitor.pythonPath' setting.`);
        });

        this.agentProcess.on('close', (code) => {
            this.outputChannel.appendLine(`[Bridge] Agent process exited with code ${code}`);
            this.agentProcess = null;
        });
    }

    public stop() {
        if (this.agentProcess) {
            this.agentProcess.kill();
            this.agentProcess = null;
        }
    }

    public pause() {
        vscode.window.showInformationMessage("Janitor: Watching paused.");
    }

    public forceUpdate() {
        vscode.window.showInformationMessage("Janitor: Forcing documentation update...");
    }

    public openLastDiff() {
        this.outputChannel.appendLine("[Bridge] Opening last diff (stub)");
    }

    public fullRegen() {
        this.outputChannel.appendLine("[Bridge] Starting full-repo regeneration (Pro)");
    }

    public onStatusUpdate(callback: (status: any) => void) {
        this.statusListeners.push(callback);
    }

    private notifyListeners(status: any) {
        this.statusListeners.forEach(l => l(status));
    }
}
