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

    public start() {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        const agentPath = path.join(this.context.extensionPath, '..', 'agent', 'main.py');
        const pythonPath = 'C:\\Users\\s314l\\miniconda3\\python.exe';

        this.outputChannel.appendLine(`[Bridge] Agent script: ${agentPath}`);
        this.outputChannel.appendLine(`[Bridge] Working dir: ${workspaceFolder}`);
        this.outputChannel.show();

        this.agentProcess = spawn(pythonPath, [agentPath], {
            cwd: workspaceFolder
        });

        this.agentProcess.stdout?.on('data', (data) => {
            this.stdoutBuffer += data.toString();
            const lines = this.stdoutBuffer.split('\n');
            // Keep the last (possibly incomplete) line in the buffer
            this.stdoutBuffer = lines.pop() || '';
            
            for (const line of lines) {
                const trimmed = line.trim();
                this.outputChannel.appendLine(`[Line]: ${trimmed}`);
                
                if (trimmed.startsWith('{')) {
                    try {
                        const payload = JSON.parse(trimmed);
                        if (payload.event) {
                            this.outputChannel.appendLine(`[Parsed OK]: event=${payload.event}, tier=${payload.tier}`);
                            this.notifyListeners(payload);
                            if (payload.event === 'updated') {
                                vscode.window.showInformationMessage(`Janitor: ${payload.summary}`);
                            }
                        }
                    } catch (e) {
                        this.outputChannel.appendLine(`[Parse Failed]: ${trimmed.substring(0, 80)}...`);
                    }
                }
            }
        });

        this.agentProcess.stderr?.on('data', (data) => {
            this.outputChannel.appendLine(`[Agent Error]: ${data}`);
        });

        this.agentProcess.on('close', (code) => {
            this.outputChannel.appendLine(`[Bridge] Agent exited with code ${code}`);
        });
    }

    public onStatusUpdate(callback: (status: any) => void) {
        this.statusListeners.push(callback);
    }

    private notifyListeners(status: any) {
        this.statusListeners.forEach(l => l(status));
    }

    public pause() {
        // Send pause signal to agent
    }

    public forceUpdate() {
        // Send force update signal to agent
    }

    public openLastDiff() {
        // logic to open diff editor
    }

    public fullRegen() {
        // Send signal to agent for full repo regeneration
        this.outputChannel.appendLine("[AllScale]: Full-repo regeneration triggered via micropayment.");
    }
}
