const express = require('express');
const { Server } = require('socket.io');
const http = require('http');
const path = require('path');
const { LingmaClient } = require('@ali/lingma-sdk');
const yaml = require('yaml');
const fs = require('fs');

class LingmaAssistant {
    constructor() {
        this.app = express();
        this.server = http.createServer(this.app);
        this.io = new Server(this.server, {
            cors: {
                origin: "*",
                methods: ["GET", "POST"]
            }
        });
        
        this.lingmaClient = null;
        this.setupRoutes();
        this.setupSocketIO();
        this.setupLingma();
    }

    setupLingma() {
        try {
            // 初始化Lingma客户端
            this.lingmaClient = new LingmaClient({
                appId: process.env.LINGMA_APP_ID || 'your-app-id',
                appSecret: process.env.LINGMA_APP_SECRET || 'your-app-secret',
                endpoint: process.env.LINGMA_ENDPOINT || 'https://lingma.aliyun.com'
            });
            
            console.log('Lingma客户端初始化成功');
        } catch (error) {
            console.error('Lingma客户端初始化失败:', error);
        }
    }

    setupRoutes() {
        // 静态文件服务
        this.app.use(express.static(path.join(__dirname, 'public')));
        
        // API路由
        this.app.use('/api', require('./routes/api'));
        
        // 健康检查
        this.app.get('/health', (req, res) => {
            res.json({ status: 'ok', timestamp: new Date().toISOString() });
        });
        
        // 主页
        this.app.get('/', (req, res) => {
            res.sendFile(path.join(__dirname, 'public', 'index.html'));
        });
    }

    setupSocketIO() {
        this.io.on('connection', (socket) => {
            console.log('用户连接:', socket.id);
            
            // 工具生成请求
            socket.on('generate-tool', async (data) => {
                try {
                    const { description, options } = data;
                    socket.emit('generation-progress', { status: 'started', message: '开始生成工具...' });
                    
                    const result = await this.generateTool(description, options);
                    socket.emit('generation-complete', result);
                    
                } catch (error) {
                    socket.emit('generation-error', { error: error.message });
                }
            });
            
            // 代码分析请求
            socket.on('analyze-code', async (data) => {
                try {
                    const { code, filePath } = data;
                    const analysis = await this.analyzeCode(code, filePath);
                    socket.emit('analysis-result', analysis);
                } catch (error) {
                    socket.emit('analysis-error', { error: error.message });
                }
            });
            
            // 实时调试会话
            socket.on('debug-session', async (data) => {
                try {
                    const { sessionId, action, payload } = data;
                    const result = await this.handleDebugSession(sessionId, action, payload);
                    socket.emit('debug-response', result);
                } catch (error) {
                    socket.emit('debug-error', { error: error.message });
                }
            });
            
            socket.on('disconnect', () => {
                console.log('用户断开连接:', socket.id);
            });
        });
    }

    async generateTool(description, options = {}) {
        // 使用Lingma进行智能工具生成
        if (this.lingmaClient) {
            try {
                // 调用Lingma的代码生成能力
                const prompt = this.createGenerationPrompt(description, options);
                
                const response = await this.lingmaClient.chat({
                    messages: [
                        {
                            role: 'system',
                            content: '你是一个专业的DCC和UE工具开发专家，擅长根据需求生成高质量的工具代码。'
                        },
                        {
                            role: 'user',
                            content: prompt
                        }
                    ],
                    temperature: 0.7,
                    maxTokens: 2000
                });
                
                return this.processLingmaResponse(response, description);
                
            } catch (error) {
                console.error('Lingma调用失败:', error);
                // 降级到本地处理
                return this.localToolGeneration(description, options);
            }
        } else {
            // 本地处理
            return this.localToolGeneration(description, options);
        }
    }

    createGenerationPrompt(description, options) {
        return `
请根据以下描述生成一个完整的DCC/UE工具：

描述: ${description}

要求:
1. 生成符合SDD规范的配置文件
2. 创建完整的Python插件代码
3. 包含参数验证和错误处理
4. 提供使用示例和文档
5. 遵循最佳实践和安全规范

选项设置:
${JSON.stringify(options, null, 2)}

请按照以下结构输出:
[SDD_CONFIG]
YAML格式的SDD配置

[PLUGIN_CODE]
完整的插件代码

[DOCUMENTATION]
使用说明文档
`;
    }

    processLingmaResponse(response, originalDescription) {
        const content = response.choices[0].message.content;
        
        // 解析Lingma的响应
        const sections = {
            sddConfig: this.extractSection(content, 'SDD_CONFIG'),
            pluginCode: this.extractSection(content, 'PLUGIN_CODE'),
            documentation: this.extractSection(content, 'DOCUMENTATION')
        };
        
        // 保存生成的文件
        const toolName = this.extractToolName(originalDescription);
        const outputPath = path.join(process.cwd(), 'generated_tools', toolName);
        
        if (!fs.existsSync(outputPath)) {
            fs.mkdirSync(outputPath, { recursive: true });
        }
        
        // 保存配置文件
        if (sections.sddConfig) {
            const config = yaml.parse(sections.sddConfig);
            fs.writeFileSync(
                path.join(outputPath, `${toolName}_config.yaml`),
                yaml.stringify(config)
            );
        }
        
        // 保存插件代码
        if (sections.pluginCode) {
            fs.writeFileSync(
                path.join(outputPath, 'plugin.py'),
                sections.pluginCode
            );
        }
        
        // 保存文档
        if (sections.documentation) {
            fs.writeFileSync(
                path.join(outputPath, 'README.md'),
                sections.documentation
            );
        }
        
        return {
            success: true,
            toolName: toolName,
            outputPath: outputPath,
            files: Object.keys(sections).filter(key => sections[key]).length
        };
    }

    extractSection(content, sectionName) {
        const pattern = new RegExp(`\\[${sectionName}\\]\\s*([\\s\\S]*?)(?=\\[|$)`, 'i');
        const match = content.match(pattern);
        return match ? match[1].trim() : '';
    }

    extractToolName(description) {
        // 从描述中提取工具名称
        const nameMatch = description.match(/(?:创建|开发|制作)\s*一个?\s*([^，。的]+)/i);
        return nameMatch ? nameMatch[1].trim().replace(/\s+/g, '') : 'GeneratedTool';
    }

    async localToolGeneration(description, options) {
        // 本地工具生成逻辑（备用方案）
        const toolName = this.extractToolName(description);
        
        const basicPlugin = `
"""
${toolName} - ${description}
"""

PLUGIN_NAME = "${toolName}"
PLUGIN_VERSION = "1.0.0"
PLUGIN_TYPE = "utility"
PLUGIN_DESCRIPTION = "${description}"
PLUGIN_AUTHOR = "Lingma Assistant"

def execute(**kwargs):
    """执行函数"""
    print(f"执行 {PLUGIN_NAME}")
    print(f"参数: {kwargs}")
    return {"status": "success", "result": "工具执行完成"}

def register():
    """注册函数"""
    return {
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "execute": execute
    }
`;
        
        const outputPath = path.join(process.cwd(), 'generated_tools', toolName);
        if (!fs.existsSync(outputPath)) {
            fs.mkdirSync(outputPath, { recursive: true });
        }
        
        fs.writeFileSync(path.join(outputPath, 'plugin.py'), basicPlugin);
        
        return {
            success: true,
            toolName: toolName,
            outputPath: outputPath,
            files: 1,
            method: 'local'
        };
    }

    async analyzeCode(code, filePath) {
        // 代码分析功能
        const analysis = {
            filePath: filePath,
            lineCount: code.split('\n').length,
            complexity: this.calculateComplexity(code),
            issues: await this.findIssues(code),
            suggestions: await this.getSuggestions(code)
        };
        
        return analysis;
    }

    calculateComplexity(code) {
        // 简单的复杂度计算
        const lines = code.split('\n');
        const functionCount = lines.filter(line => line.trim().startsWith('def ')).length;
        const classCount = lines.filter(line => line.trim().startsWith('class ')).length;
        const ifElseCount = (code.match(/if|elif|else/g) || []).length;
        
        return {
            functions: functionCount,
            classes: classCount,
            branches: ifElseCount,
            cyclomatic: ifElseCount + 1
        };
    }

    async findIssues(code) {
        // 查找常见问题
        const issues = [];
        
        if (!code.includes('PLUGIN_NAME')) {
            issues.push({
                type: 'missing_constant',
                message: '缺少PLUGIN_NAME常量',
                severity: 'error'
            });
        }
        
        if (!code.includes('execute') && !code.includes('main')) {
            issues.push({
                type: 'missing_function',
                message: '缺少执行函数',
                severity: 'error'
            });
        }
        
        return issues;
    }

    async getSuggestions(code) {
        // 提供改进建议
        const suggestions = [];
        
        if (code.includes('print(') && !code.includes('logging')) {
            suggestions.push({
                type: 'logging',
                message: '建议使用logging模块替代print进行日志输出'
            });
        }
        
        if (code.length > 1000 && !code.includes('class ')) {
            suggestions.push({
                type: 'structure',
                message: '长代码建议使用类来组织结构'
            });
        }
        
        return suggestions;
    }

    async handleDebugSession(sessionId, action, payload) {
        // 处理调试会话
        switch (action) {
            case 'start':
                return await this.startDebugSession(sessionId, payload);
            case 'step':
                return await this.stepDebugSession(sessionId, payload);
            case 'stop':
                return await this.stopDebugSession(sessionId);
            default:
                throw new Error(`未知的调试操作: ${action}`);
        }
    }

    async startDebugSession(sessionId, payload) {
        // 启动调试会话
        return {
            sessionId: sessionId,
            status: 'running',
            breakpoints: []
        };
    }

    async stepDebugSession(sessionId, payload) {
        // 单步调试
        return {
            sessionId: sessionId,
            status: 'paused',
            currentLine: payload.line || 1
        };
    }

    async stopDebugSession(sessionId) {
        // 停止调试会话
        return {
            sessionId: sessionId,
            status: 'stopped'
        };
    }

    start(port = 3000) {
        this.server.listen(port, () => {
            console.log(`Lingma助手服务启动在端口 ${port}`);
            console.log(`访问地址: http://localhost:${port}`);
        });
    }
}

// 启动服务
const assistant = new LingmaAssistant();
const PORT = process.env.PORT || 3000;
assistant.start(PORT);

module.exports = LingmaAssistant;