# AI辅助学术研究工作台

专为生物信息学/生命科学研究生设计的本地Web工具，帮助你在科研中系统化地使用大模型（DeepSeek、Kimi等）完成文献调研、方法对比、代码辅助和论文写作等任务。

## 核心设计理念

- **阶段化引导**：将科研流程划分为5个标准阶段，提供对应的结构化提问模板
- **模板化输入**：内置经过优化的提示词模板，用户只需填写关键占位符
- **对话历史管理**：每个研究项目保存完整的多轮对话记录，支持随时回溯
- **输出结构化**：AI回复自动解析为Markdown表格、代码块或纯文本
- **验证提醒机制**：关键节点自动弹出核查清单，提醒交叉验证

## 五个科研阶段

| 阶段 | 用途 |
|------|------|
| 文献调研 | 快速锁定核心文献，发现研究空白 |
| 方法对比 | 对比不同方法/工具的异同 |
| 方案设计 | 设计实验流程和对照组 |
| 数据分析 | 辅助生成、调试、解释代码 |
| 论文写作 | 生成大纲、段落、PPT结构 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API

在左侧边栏的「API设置」中填写：
- **API Base URL**：例如 `https://api.deepseek.com` 或 `https://api.moonshot.cn`
- **API Key**：你的API密钥
- **模型名称**：例如 `deepseek-chat` 或 `moonshot-v1-8k`

### 3. 启动应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开（默认地址 http://localhost:8501）。

## 项目结构

```
ai-academic-workbench/
├── app.py              # Streamlit主应用
├── config.py           # 全局配置
├── project_manager.py  # 项目管理模块
├── llm_client.py       # 大模型API客户端
├── templates.json      # 提示词模板（可自定义扩展）
├── requirements.txt    # 依赖包列表
├── projects/           # 项目数据存储目录（自动创建）
└── config.json         # API配置存储（自动创建）
```

## 自定义模板

编辑 `templates.json` 文件，按阶段添加新的提示词模板。模板中的占位符使用 `{{}}` 包裹，例如 `{{研究主题}}`。

## 数据隐私

所有项目数据以JSON格式保存在本地 `./projects/` 目录，不上传至任何云端服务，充分保护研究隐私。

## 技术栈

- **前端框架**：Streamlit（纯Python，便于本地运行和修改）
- **后端逻辑**：Python 3.9+
- **API集成**：OpenAI格式接口（兼容DeepSeek、Kimi等）
- **数据存储**：本地JSON文件

## 许可证

MIT License
