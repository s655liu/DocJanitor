import * as vscode from 'vscode';

export class StatusBarManager {
    private item: vscode.StatusBarItem;

    constructor() {
        this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.item.text = "$(eye) Janitor: watching";
        this.item.show();
    }

    public update(status: any) {
        if (status.event === 'updating') {
            const modelTag = status.model ? ` [${status.model}]` : '';
            this.item.text = `$(sync~spin) Janitor: updating docs...${modelTag}`;
            this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        } else {
            this.item.text = `$(check) Janitor: idle`;
            this.item.backgroundColor = undefined;
            
            setTimeout(() => {
                this.item.text = "$(eye) Janitor: watching";
            }, 5000);
        }
    }
}
