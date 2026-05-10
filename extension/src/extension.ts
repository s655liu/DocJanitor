import * as vscode from 'vscode';
import { AgentBridge } from './agentBridge';
import { SidebarProvider } from './sidebar';
import { StatusBarManager } from './statusBar';

export function activate(context: vscode.ExtensionContext) {
    console.log('Auto-Doc Janitor is now active!');

    const outputChannel = vscode.window.createOutputChannel('Auto-Doc Janitor');
    const statusBar = new StatusBarManager();
    const sidebar = new SidebarProvider(context.extensionUri);
    const agentBridge = new AgentBridge(context, outputChannel);

    // Register Sidebar
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('autodoc-janitor-sidebar', sidebar)
    );

    // Link components
    agentBridge.onStatusUpdate((status) => {
        statusBar.update(status);
        sidebar.update(status);
        if (status.reasoning) {
            outputChannel.appendLine(`[REASONING]: ${status.reasoning}`);
        }
    });

    // Start Agent
    agentBridge.start();

    // Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('janitor.pause', () => agentBridge.pause()),
        vscode.commands.registerCommand('janitor.forceUpdate', () => agentBridge.forceUpdate()),
        vscode.commands.registerCommand('janitor.openDiff', () => agentBridge.openLastDiff()),
        vscode.commands.registerCommand('janitor.fullRegen', async () => {
            const choice = await vscode.window.showInformationMessage(
                "Full-Repo Architecture Regeneration is a Pro feature ($0.50). Proceed to AllScale Checkout?",
                "Pay with AllScale", "Cancel"
            );
            if (choice === "Pay with AllScale") {
                vscode.window.showInformationMessage("AllScale: Payment successful! Starting full regeneration...");
                agentBridge.fullRegen();
            }
        })
    );
}

export function deactivate() {
    // Cleanup agent process
}
