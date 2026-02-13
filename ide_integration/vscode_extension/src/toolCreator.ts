import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export class ToolCreator {
    async createToolFromDescription(): Promise<void> {
        try {
            // 获取用户输入的工具描述
            const description = await vscode.window.showInputBox({
                prompt: '请输入工具描述',
                placeHolder: '例如：创建一个Maya的网格清理工具，能够删除重复顶点...'
            });

            if (!description) {
                return;
            }

            // 获取输出目录
            const config = vscode.workspace.getConfiguration('dccue');
            const outputDir = config.get('defaultOutputDir', './generated_tools');
            
            // 确保输出目录存在
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, { recursive: true });
            }

            // 显示进度
            const progressOptions: vscode.ProgressOptions = {
                location: vscode.ProgressLocation.Notification,
                title: '正在生成工具...',
                cancellable: true
            };

            await vscode.window.withProgress(progressOptions, async (progress, token) => {
                token.onCancellationRequested(() => {
                    vscode.window.showInformationMessage('工具生成已取消');
                });

                try {
                    progress.report({ message: '调用AI生成工具...', increment: 30 });
                    
                    // 调用Python后端生成工具
                    const pythonPath = this.getPythonPath();
                    const scriptPath = path.join(__dirname, '../../scripts/generate_tool.py');
                    
                    const { stdout, stderr } = await execAsync(
                        `${pythonPath} "${scriptPath}" "${description}" "${outputDir}"`
                    );

                    if (stderr) {
                        throw new Error(stderr);
                    }

                    progress.report({ message: '工具生成完成', increment: 100 });
                    
                    // 解析结果
                    const result = JSON.parse(stdout);
                    
                    if (result.success) {
                        vscode.window.showInformationMessage(
                            `工具生成成功: ${result.tool_name}`,
                            '在资源管理器中查看',
                            '打开工具目录'
                        ).then(selection => {
                            if (selection === '在资源管理器中查看') {
                                const toolPath = vscode.Uri.file(result.tool_path);
                                vscode.commands.executeCommand('revealInExplorer', toolPath);
                            } else if (selection === '打开工具目录') {
                                const toolPath = vscode.Uri.file(result.tool_path);
                                vscode.commands.executeCommand('vscode.openFolder', toolPath, true);
                            }
                        });

                        // 在终端中显示生成的文件
                        this.showGeneratedFiles(result.generated_files);
                    } else {
                        vscode.window.showErrorMessage(`工具生成失败: ${result.error}`);
                    }

                } catch (error) {
                    vscode.window.showErrorMessage(`生成工具时出错: ${error}`);
                }
            });

        } catch (error) {
            vscode.window.showErrorMessage(`创建工具失败: ${error}`);
        }
    }

    private getPythonPath(): string {
        // 尝试获取Python路径
        const pythonPath = vscode.workspace.getConfiguration('python').get('defaultInterpreterPath');
        return pythonPath ? `"${pythonPath}"` : 'python';
    }

    private showGeneratedFiles(files: string[]): void {
        const outputChannel = vscode.window.createOutputChannel('DCC/UE Tool Generator');
        outputChannel.show();
        outputChannel.appendLine('生成的文件:');
        files.forEach(file => {
            outputChannel.appendLine(`  - ${file}`);
        });
        outputChannel.appendLine('\n使用说明:');
        outputChannel.appendLine('1. 检查生成的代码是否符合需求');
        outputChannel.appendLine('2. 安装必要的依赖: pip install -r requirements.txt');
        outputChannel.appendLine('3. 运行测试: python test_*.py');
        outputChannel.appendLine('4. 集成到框架中使用');
    }
}