"""
全局配置文件
定义路径常量、默认配置和全局变量
"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据存储目录
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")

# 配置文件路径
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# 模板文件路径
TEMPLATES_FILE = os.path.join(BASE_DIR, "templates.json")

# 确保目录存在
def ensure_directories():
    """
    确保必要的目录和文件存在
    第一次运行时自动创建
    """
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)

# 五个科研阶段定义
STAGES = [
    {"id": "literature", "name": "文献调研", "icon": "📚"},
    {"id": "comparison", "name": "方法对比", "icon": "⚖️"},
    {"id": "design", "name": "方案设计", "icon": "📝"},
    {"id": "analysis", "name": "数据分析", "icon": "🔬"},
    {"id": "writing", "name": "论文写作", "icon": "✍️"},
]

# 阶段ID到名称的映射
STAGE_MAP = {s["id"]: s["name"] for s in STAGES}
