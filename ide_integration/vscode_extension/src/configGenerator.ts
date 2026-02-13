import * as vscode from 'vscode';
import * as yaml from 'yaml';
import axios from 'axios';

export class ConfigGenerator {
    async generateFromSelection(): Promise<void> {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('请先打开一个文件并选择文本');
                return;
            }

            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);

            if (!selectedText.trim()) {
                vscode.window.showErrorMessage('请选择要转换为配置的文本');
                return;
            }

            // 显示快速选择框让用户选择目标格式
            const format = await vscode.window.showQuickPick(
                ['SDD YAML', 'SDD JSON', 'Plugin Config'],
                {
                    placeHolder: '选择生成的配置格式'
                }
            );

            if (!format) {
                return;
            }

            // 显示进度
            await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: '正在生成配置...',
                    cancellable: false
                },
                async (progress) => {
                    progress.report({ message: '处理选中文本...', increment: 30 });

                    try {
                        const config = await this.processTextToConfig(selectedText, format);
                        
                        progress.report({ message: '生成配置完成', increment: 100 });

                        // 创建新文件或插入到当前位置
                        const action = await vscode.window.showQuickPick(
                            ['创建新文件', '插入到当前位置'],
                            { placeHolder: '如何处理生成的配置?' }
                        );

                        if (action === '创建新文件') {
                            await this.createConfigFile(config, format);
                        } else {
                            await this.insertConfigAtCursor(config);
                        }

                        vscode.window.showInformationMessage('配置生成成功!');

                    } catch (error) {
                        vscode.window.showErrorMessage(`生成配置失败: ${error}`);
                    }
                }
            );

        } catch (error) {
            vscode.window.showErrorMessage(`配置生成出错: ${error}`);
        }
    }

    private async processTextToConfig(text: string, format: string): Promise<any> {
        const config = vscode.workspace.getConfiguration('dccue');
        const aiProvider = config.get('aiProvider', 'openai');
        const apiKey = config.get('apiKey', '');

        // 如果配置了AI，使用AI处理
        if (apiKey && aiProvider !== 'local') {
            return await this.callAiService(text, format, aiProvider, apiKey);
        } else {
            // 使用本地规则处理
            return this.localTextProcessing(text, format);
        }
    }

    private async callAiService(text: string, format: string, provider: string, apiKey: string): Promise<any> {
        const prompt = this.createPrompt(text, format);
        
        try {
            let response;
            
            if (provider === 'openai') {
                response = await axios.post('https://api.openai.com/v1/chat/completions', {
                    model: 'gpt-3.5-turbo',
                    messages: [
                        {
                            role: 'system',
                            content: '你是一个专业的配置文件生成专家，专门将自然语言描述转换为标准化的配置格式。'
                        },
                        {
                            role: 'user',
                            content: prompt
                        }
                    ],
                    temperature: 0.7
                }, {
                    headers: {
                        'Authorization': `Bearer ${apiKey}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                const aiResponse = response.data.choices[0].message.content;
                return this.parseAiResponse(aiResponse, format);
                
            } else if (provider === 'anthropic') {
                // Anthropic API调用
                response = await axios.post('https://api.anthropic.com/v1/messages', {
                    model: 'claude-3-haiku-20240307',
                    messages: [{ role: 'user', content: prompt }],
                    max_tokens: 1000
                }, {
                    headers: {
                        'x-api-key': apiKey,
                        'Content-Type': 'application/json'
                    }
                });
                
                const aiResponse = response.data.content[0].text;
                return this.parseAiResponse(aiResponse, format);
            }
            
        } catch (error) {
            vscode.window.showWarningMessage('AI服务调用失败，使用本地处理');
            return this.localTextProcessing(text, format);
        }
    }

    private createPrompt(text: string, format: string): string {
        return `
请将以下自然语言描述转换为${format}格式的配置：

${text}

要求：
1. 严格遵循SDD规范格式
2. 提取关键信息：工具名称、类型、参数、依赖等
3. 保持配置的完整性和准确性
4. 只输出配置内容，不要添加解释说明

输出格式：
${format === 'SDD YAML' ? 'YAML格式的SDD配置' : 
  format === 'SDD JSON' ? 'JSON格式的SDD配置' : 
  '插件配置格式'}
`;
    }

    private parseAiResponse(response: string, format: string): any {
        try {
            if (format.includes('YAML')) {
                return yaml.parse(response);
            } else if (format.includes('JSON')) {
                return JSON.parse(response);
            } else {
                // 简单的键值对解析
                const config: any = {};
                const lines = response.split('\n');
                for (const line of lines) {
                    const [key, value] = line.split(':').map(s => s.trim());
                    if (key && value) {
                        config[key] = value;
                    }
                }
                return config;
            }
        } catch (error) {
            throw new Error('AI响应解析失败');
        }
    }

    private localTextProcessing(text: string, format: string): any {
        // 简单的本地文本处理规则
        const config: any = {
            tool: {
                name: this.extractToolName(text) || 'GeneratedTool',
                version: '1.0.0',
                type: this.extractToolType(text) || 'utility',
                description: text.substring(0, 100) + (text.length > 100 ? '...' : '')
            },
            metadata: {
                author: 'VSCode Extension',
                created_date: new Date().toISOString().split('T')[0]
            },
            configuration: {
                parameters: this.extractParameters(text)
            }
        };

        return config;
    }

    private extractToolName(text: string): string {
        // 提取工具名称的简单规则
        const namePatterns = [
            /(?:创建|开发|制作)\s*一个?\s*([^，。的]+)/i,
            /([^，。的]+?)\s*(?:工具|插件|功能)/i
        ];
        
        for (const pattern of namePatterns) {
            const match = text.match(pattern);
            if (match) {
                return match[1].trim();
            }
        }
        return '';
    }

    private extractToolType(text: string): string {
        const dccKeywords = ['maya', '3ds max', 'blender', 'dcc'];
        const ueKeywords = ['unreal', 'ue', '虚幻'];
        
        const lowerText = text.toLowerCase();
        
        if (dccKeywords.some(keyword => lowerText.includes(keyword))) {
            return 'dcc';
        } else if (ueKeywords.some(keyword => lowerText.includes(keyword))) {
            return 'ue_engine';
        }
        return 'utility';
    }

    private extractParameters(text: string): any[] {
        const parameters: any[] = [];
        
        // 简单的参数提取规则
        const paramPatterns = [
            /([^，。\s]+?)[:：]\s*([^，。\s]+)/g,
            /(?:参数|选项)\s*[:：]?\s*([^，。]+)/g
        ];
        
        for (const pattern of paramPatterns) {
            let match;
            while ((match = pattern.exec(text)) !== null) {
                if (match[1] && match[1].length > 1) {
                    parameters.push({
                        name: match[1].trim(),
                        type: 'string',
                        required: false,
                        description: match[2] ? match[2].trim() : ''
                    });
                }
            }
        }
        
        return parameters.length > 0 ? parameters : [];
    }

    private async createConfigFile(config: any, format: string): Promise<void> {
        const fileName = `tool_config.${format.includes('YAML') ? 'yaml' : 'json'}`;
        const workspaceUri = vscode.workspace.workspaceFolders?.[0]?.uri;
        
        if (workspaceUri) {
            const configUri = vscode.Uri.joinPath(workspaceUri, fileName);
            const content = format.includes('YAML') 
                ? yaml.stringify(config) 
                : JSON.stringify(config, null, 2);
            
            await vscode.workspace.fs.writeFile(configUri, Buffer.from(content, 'utf8'));
            await vscode.window.showTextDocument(configUri);
        }
    }

    private async insertConfigAtCursor(config: any): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const content = yaml.stringify(config);
            await editor.edit(editBuilder => {
                editBuilder.insert(editor.selection.active, content);
            });
        }
    }
}