import * as vscode from 'vscode';
import { ToolCreator } from './toolCreator';
import { ConfigGenerator } from './configGenerator';
import { ToolValidator } from './toolValidator';
import { ToolRunner } from './toolRunner';
import { AiAssistantView } from './aiAssistantView';
import { ToolsExplorer } from './toolsExplorer';

export function activate(context: vscode.ExtensionContext) {
    console.log('DCC/UE Tool Framework extension is now active!');

    // 初始化各个组件
    const toolCreator = new ToolCreator();
    const configGenerator = new ConfigGenerator();
    const toolValidator = new ToolValidator();
    const toolRunner = new ToolRunner();
    
    // 注册命令
    const createToolDisposable = vscode.commands.registerCommand(
        'dccue.createTool', 
        () => toolCreator.createToolFromDescription()
    );
    
    const generateConfigDisposable = vscode.commands.registerCommand(
        'dccue.generateConfig',
        () => configGenerator.generateFromSelection()
    );
    
    const validateToolDisposable = vscode.commands.registerCommand(
        'dccue.validateTool',
        (uri?: vscode.Uri) => toolValidator.validateTool(uri)
    );
    
    const runToolDisposable = vscode.commands.registerCommand(
        'dccue.runTool',
        () => toolRunner.runCurrentTool()
    );
    
    const debugToolDisposable = vscode.commands.registerCommand(
        'dccue.debugTool',
        () => toolRunner.debugCurrentTool()
    );

    // 注册视图
    const toolsExplorer = new ToolsExplorer(context);
    const aiAssistantView = new AiAssistantView(context);

    // 注册树视图
    const toolsTreeView = vscode.window.createTreeView('dccueToolsView', {
        treeDataProvider: toolsExplorer
    });

    const aiAssistantTreeView = vscode.window.createTreeView('dccueAiAssistant', {
        treeDataProvider: aiAssistantView
    });

    // 添加到订阅
    context.subscriptions.push(
        createToolDisposable,
        generateConfigDisposable,
        validateToolDisposable,
        runToolDisposable,
        debugToolDisposable,
        toolsTreeView,
        aiAssistantTreeView
    );

    // 设置状态
    vscode.commands.executeCommand('setContext', 'dccue:enabled', true);

    // 监听文件变化
    if (vscode.workspace.workspaceFolders) {
        const watcher = vscode.workspace.createFileSystemWatcher(
            '**/*.{py,yaml,yml}',
            false,
            false,
            false
        );
        
        watcher.onDidChange(() => {
            if (vscode.workspace.getConfiguration('dccue').get('enableAutoValidation')) {
                toolValidator.autoValidate();
            }
        });
        
        context.subscriptions.push(watcher);
    }
}

export function deactivate() {
    console.log('DCC/UE Tool Framework extension is now deactivated!');
}