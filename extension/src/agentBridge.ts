import * as vscode from 'vscode';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';

export class AgentBridge {
    private agentProcess: ChildProcess | null = null;
    private statusListeners: ((status: any) => void)[] = [];

    constructor(
        private context: vscode.ExtensionContext,
        private outputChannel: vscode.OutputChannel
    ) {}

    public start() {
        const agentPath = path.join(this.context.extensionPath, '..', 'agent', 'main.py');
        const pythonPath = 'python'; // Should be configurable

        console.log(`Spawning agent: ${pythonPath} ${agentPath}`);

        this.agentProcess = spawn(pythonPath, [agentPath], {
            cwd: vscode.workspace.workspaceFolders?.[0].uri.fsPath
        });

        this.agentProcess.stdout?.on('data', (data) => {
            this.outputChannel.appendLine(`Agent Stdout: ${data}`);
            try {
                const payload = JSON.parse(data.toString());
                this.notifyListeners(payload);
            } catch (e) {
                console.log(`Agent output: ${data}`);
            }
        });

        this.agentProcess.stderr?.on('data', (data) => {
            console.error(`Agent error: ${data}`);
        });

        this.agentProcess.on('close', (code) => {
            console.log(`Agent process exited with code ${code}`);
            // Handle restart logic
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
