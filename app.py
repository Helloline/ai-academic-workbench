"""
AI辅助学术研究工作台 - Streamlit主应用
面向生物信息学/生命科学研究生的本地Web工具

功能：
- 阶段化科研流程引导（文献调研、方法对比、方案设计、数据分析、论文写作）
- 模板化提示词输入
- 对话历史管理
- 输出结构化展示
- 核查提醒机制
"""
import json
import os
import sys
import re

import streamlit as st

from config import STAGES, STAGE_MAP, TEMPLATES_FILE, ensure_directories
from project_manager import (
    get_all_projects,
    create_project,
    load_project,
    save_project,
    delete_project,
    add_chat_message,
    mark_message_verified,
)
from llm_client import load_api_config, save_api_config, chat_completion

# 页面配置
st.set_page_config(
    page_title="AI辅助学术研究工作台",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义CSS样式
st.markdown("""
<style>
    .stage-btn {
        border-radius: 8px;
        padding: 8px 16px;
        margin: 2px;
        font-weight: 500;
    }
    .chat-user {
        background-color: #e3f2fd;
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #2196f3;
    }
    .chat-assistant {
        background-color: #f5f5f5;
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #4caf50;
    }
    .chat-assistant-verified {
        background-color: #e8f5e9;
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #4caf50;
        border: 2px solid #4caf50;
    }
    .template-card {
        background-color: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        margin: 6px 0;
        cursor: pointer;
    }
    .template-card:hover {
        background-color: #f0f0f0;
        border-color: #bdbdbd;
    }
    .verify-box {
        background-color: #fff3e0;
        border: 1px solid #ff9800;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
    }
    .sidebar-project {
        padding: 8px;
        border-radius: 6px;
        margin: 4px 0;
    }
    .sidebar-project:hover {
        background-color: #f5f5f5;
    }
    .sidebar-project-active {
        background-color: #e3f2fd;
        border-left: 3px solid #2196f3;
    }
    /* 代码块样式优化 */
    pre {
        background-color: #263238 !important;
        color: #aed581 !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }
    /* 表格样式 */
    .stMarkdown table {
        border-collapse: collapse;
        width: 100%;
    }
    .stMarkdown th, .stMarkdown td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .stMarkdown th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# ============ 初始化Session State ============
def init_session_state():
    """初始化Streamlit的session state变量"""
    defaults = {
        "current_project": None,
        "current_stage": "literature",
        "chat_input": "",
        "show_verify_modal": False,
        "verify_message_index": None,
        "verify_note": "",
        "show_new_project": False,
        "show_api_settings": False,
        "api_base_url": "",
        "api_key": "",
        "api_model": "deepseek-chat",
        "template_selected": None,
        "pending_template": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # 加载已保存的API配置
    cfg = load_api_config()
    if cfg.get("base_url") and not st.session_state["api_base_url"]:
        st.session_state["api_base_url"] = cfg.get("base_url", "")
    if cfg.get("api_key") and not st.session_state["api_key"]:
        st.session_state["api_key"] = cfg.get("api_key", "")
    if cfg.get("model") and not st.session_state["api_model"]:
        st.session_state["api_model"] = cfg.get("model", "deepseek-chat")


init_session_state()
ensure_directories()


# ============ 加载模板 ============
@st.cache_data
def load_templates():
    """
    加载提示词模板
    从templates.json读取，支持用户自定义扩展

    Returns:
        dict: 按阶段分类的模板字典
    """
    if os.path.exists(TEMPLATES_FILE):
        try:
            with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ============ 侧边栏 ============
with st.sidebar:
    st.title("🔬 AI学术工作台")
    st.markdown("---")

    # API设置
    with st.expander("🔧 API设置", expanded=False):
        st.markdown("支持DeepSeek、Kimi等OpenAI格式接口")
        base_url = st.text_input(
            "API Base URL",
            value=st.session_state["api_base_url"],
            placeholder="https://api.deepseek.com",
            help="例如：https://api.deepseek.com 或 https://api.moonshot.cn",
        )
        api_key = st.text_input(
            "API Key",
            value=st.session_state["api_key"],
            type="password",
            placeholder="sk-...",
        )
        model = st.text_input(
            "模型名称",
            value=st.session_state["api_model"],
            placeholder="deepseek-chat",
        )
        if st.button("💾 保存配置", use_container_width=True):
            save_api_config(base_url, api_key, model)
            st.session_state["api_base_url"] = base_url
            st.session_state["api_key"] = api_key
            st.session_state["api_model"] = model
            st.success("配置已保存！")

    st.markdown("---")

    # 新建项目按钮
    if st.button("➕ 新建项目", use_container_width=True):
        st.session_state["show_new_project"] = True

    # 新建项目表单
    if st.session_state["show_new_project"]:
        with st.form("new_project_form"):
            st.subheader("新建项目")
            np_name = st.text_input("项目名称 *", placeholder="例如：蛋白质-RNA相分离预测")
            np_topic = st.text_input("研究主题 *", placeholder="简要描述研究主题")
            np_keywords = st.text_input("核心关键词", placeholder="例如：machine learning, phase separation")
            np_papers = st.text_area("已知核心文献（1-2篇）", placeholder="粘贴文献标题或DOI")
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("创建", use_container_width=True)
            with col2:
                cancelled = st.form_submit_button("取消", use_container_width=True)

            if submitted:
                if not np_name or not np_topic:
                    st.error("项目名称和研究主题为必填项")
                else:
                    proj = create_project(np_name, np_topic, np_keywords, np_papers)
                    st.session_state["current_project"] = proj
                    st.session_state["show_new_project"] = False
                    st.rerun()
            if cancelled:
                st.session_state["show_new_project"] = False
                st.rerun()

    st.markdown("---")
    st.subheader("📁 项目列表")

    # 项目列表
    projects = get_all_projects()
    if not projects:
        st.info("暂无项目，点击上方「新建项目」开始")
    else:
        for proj in projects:
            is_active = (
                st.session_state["current_project"]
                and st.session_state["current_project"]["id"] == proj["id"]
            )
            css_class = "sidebar-project-active" if is_active else "sidebar-project"
            cols = st.columns([6, 1, 1])
            with cols[0]:
                if st.button(
                    f"{proj['name']}",
                    key=f"proj_{proj['id']}",
                    use_container_width=True,
                ):
                    loaded = load_project(proj["id"])
                    if loaded:
                        st.session_state["current_project"] = loaded
                        st.session_state["current_stage"] = loaded.get("current_stage", "literature")
                        st.rerun()
            with cols[1]:
                if st.button("🗑️", key=f"del_{proj['id']}", help="删除项目"):
                    delete_project(proj["id"])
                    if (
                        st.session_state["current_project"]
                        and st.session_state["current_project"]["id"] == proj["id"]
                    ):
                        st.session_state["current_project"] = None
                    st.rerun()

    # 当前项目信息展示
    if st.session_state["current_project"]:
        st.markdown("---")
        st.subheader("📋 当前项目")
        proj = st.session_state["current_project"]
        st.markdown(f"**名称：** {proj['name']}")
        st.markdown(f"**主题：** {proj['topic']}")
        if proj.get("keywords"):
            st.markdown(f"**关键词：** {proj['keywords']}")
        if proj.get("core_papers"):
            st.markdown(f"**核心文献：** {proj['core_papers'][:100]}...")


# ============ 主界面 ============
if not st.session_state["current_project"]:
    # 未选择项目时的欢迎页
    st.title("🎓 欢迎使用AI辅助学术研究工作台")
    st.markdown("""
    本工具专为**生物信息学/生命科学研究生**设计，帮助你在科研中系统化地使用大模型：

    ### 🚀 快速开始
    1. 在左侧边栏点击 **「新建项目」**
    2. 填写项目名称和研究主题
    3. 在 **「API设置」** 中配置你的大模型接口（DeepSeek/Kimi等）
    4. 按阶段使用结构化模板与AI协作

    ### 📚 五个科研阶段
    | 阶段 | 用途 |
    |------|------|
    | 📚 文献调研 | 快速锁定核心文献，发现研究空白 |
    | ⚖️ 方法对比 | 对比不同方法/工具的异同 |
    | 📝 方案设计 | 设计实验流程和对照组 |
    | 🔬 数据分析 | 辅助生成、调试、解释代码 |
    | ✍️ 论文写作 | 生成大纲、段落、PPT结构 |

    ### 💡 提示
    - 所有数据保存在本地 `./projects/` 目录，保护研究隐私
    - 可自定义提示词模板，编辑 `templates.json` 文件
    - 关键节点会自动弹出核查提醒，请务必交叉验证AI推荐内容
    """)
else:
    proj = st.session_state["current_project"]

    # 顶部标题
    st.title(f"{proj['name']}")
    st.caption(f"研究主题：{proj['topic']}  |  当前阶段：{STAGE_MAP.get(st.session_state['current_stage'], '')}")

    # 阶段切换按钮
    st.markdown("---")
    cols = st.columns(len(STAGES))
    for i, stage in enumerate(STAGES):
        with cols[i]:
            is_active = st.session_state["current_stage"] == stage["id"]
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                f"{stage['icon']} {stage['name']}",
                key=f"stage_{stage['id']}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state["current_stage"] = stage["id"]
                proj["current_stage"] = stage["id"]
                save_project(proj)
                st.rerun()

    st.markdown("---")

    # 模板选择区
    templates = load_templates()
    stage_templates = templates.get(st.session_state["current_stage"], [])

    if stage_templates:
        st.subheader("📋 提示词模板")
        st.caption("点击模板自动填入输入框，填写 `{{}}` 中的占位符即可发送")

        tpl_cols = st.columns(min(len(stage_templates), 3))
        for i, tpl in enumerate(stage_templates):
            with tpl_cols[i % len(tpl_cols)]:
                if st.button(
                    f"📄 {tpl['name']}",
                    key=f"tpl_{st.session_state['current_stage']}_{i}",
                    use_container_width=True,
                ):
                    st.session_state["pending_template"] = tpl["template"]
                    st.rerun()

    # 输入区
    st.markdown("---")
    st.subheader("💬 输入内容")

    # 如果有待填充的模板，显示在输入框
    default_text = ""
    if st.session_state.get("pending_template"):
        default_text = st.session_state["pending_template"]
        st.session_state["pending_template"] = None

    # 多行输入框
    user_input = st.text_area(
        "编辑你的提问（可修改模板内容）",
        value=default_text,
        height=150,
        key="chat_input_area",
        placeholder="在此输入内容，或从上方选择模板...",
    )

    # 发送按钮
    send_col, _ = st.columns([1, 5])
    with send_col:
        send_clicked = st.button("🚀 发送", use_container_width=True, type="primary")

    # 核查提醒弹窗（模态框模拟）
    if st.session_state.get("show_verify_modal"):
        st.markdown("---")
        with st.container():
            st.markdown("<div class='verify-box'>", unsafe_allow_html=True)
            st.subheader("⚠️ 核查提醒")
            st.markdown("""
            AI生成的内容可能存在不准确之处，请务必进行交叉验证：

            - [ ] 每篇推荐文献是否在 **PubMed/Google Scholar** 核实？
            - [ ] 推荐的工具/方法是否访问官网确认？
            - [ ] 关键数据和结论是否有可靠来源支撑？
            """)
            verify_note = st.text_input(
                "核查备注（可选）",
                value=st.session_state.get("verify_note", ""),
                placeholder="例如：PubMed确认3篇文献",
                key="verify_note_input",
            )
            vcol1, vcol2 = st.columns(2)
            with vcol1:
                if st.button("✅ 确认已核查", use_container_width=True):
                    idx = st.session_state.get("verify_message_index")
                    if idx is not None:
                        mark_message_verified(proj["id"], idx, verify_note)
                        # 刷新项目数据
                        st.session_state["current_project"] = load_project(proj["id"])
                    st.session_state["show_verify_modal"] = False
                    st.session_state["verify_message_index"] = None
                    st.session_state["verify_note"] = ""
                    st.rerun()
            with vcol2:
                if st.button("⏭️ 稍后核查", use_container_width=True):
                    st.session_state["show_verify_modal"] = False
                    st.session_state["verify_message_index"] = None
                    st.session_state["verify_note"] = ""
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # 处理发送逻辑
    if send_clicked and user_input.strip():
        stage = st.session_state["current_stage"]
        # 保存用户消息
        add_chat_message(proj["id"], "user", user_input.strip(), stage)
        # 重新加载项目以获取完整历史
        proj = load_project(proj["id"])
        st.session_state["current_project"] = proj

        # 构建消息列表
        messages = []
        for msg in proj["history"]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # 调用API（非流式，便于保存完整回复）
        with st.spinner("AI思考中..."):
            result = chat_completion(messages, stream=False)

        # 保存AI回复
        if isinstance(result, str):
            add_chat_message(proj["id"], "assistant", result, stage)
            # 文献调研和方法对比阶段自动触发核查提醒
            if stage in ("literature", "comparison"):
                st.session_state["verify_message_index"] = len(proj["history"])
                st.session_state["show_verify_modal"] = True

        # 刷新项目数据
        st.session_state["current_project"] = load_project(proj["id"])
        st.rerun()

    # 对话历史展示区
    st.markdown("---")
    st.subheader("🗨️ 对话记录")

    proj = st.session_state["current_project"]
    history = proj.get("history", [])

    if not history:
        st.info("暂无对话记录，从上方选择模板或输入内容开始提问")
    else:
        # 按阶段分组显示
        current_display_stage = None
        for idx, msg in enumerate(history):
            msg_stage = msg.get("stage", "")
            # 阶段分隔线
            if msg_stage != current_display_stage:
                current_display_stage = msg_stage
                stage_name = STAGE_MAP.get(msg_stage, msg_stage)
                st.markdown(f"""
                <div style="text-align: center; margin: 20px 0;">
                    <span style="background-color: #e0e0e0; padding: 4px 16px; border-radius: 12px; font-size: 12px; color: #616161;">
                        {stage_name}
                    </span>
                </div>
                """, unsafe_allow_html=True)

            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-user">
                    <b>👤 你</b> <span style="color: #999; font-size: 12px;">{msg.get('timestamp', '')[:16]}</span><br/>
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                verified = msg.get("verified", False)
                css = "chat-assistant-verified" if verified else "chat-assistant"
                verify_badge = "✅ 已核查" if verified else ""
                note = proj.get("verification_notes", {}).get(str(idx), "")
                note_html = f"<br/><span style='color: #4caf50; font-size: 12px;'>📝 核查备注：{note}</span>" if note else ""

                st.markdown(f"""
                <div class="{css}">
                    <b>🤖 AI</b> <span style="color: #999; font-size: 12px;">{msg.get('timestamp', '')[:16]}</span>
                    <span style="color: #4caf50; font-size: 12px; margin-left: 8px;">{verify_badge}</span>
                    {note_html}
                    <hr style="margin: 8px 0; border: none; border-top: 1px solid #ddd;">
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)

                # 操作按钮
                bcol1, bcol2, _ = st.columns([1, 1, 4])
                with bcol1:
                    # 复制按钮
                    copy_text = msg["content"].replace("`", "\\`").replace("$", "\\$")
                    st.button(
                        "📋 复制",
                        key=f"copy_{idx}",
                        on_click=lambda text=copy_text: st.write(f"<script>navigator.clipboard.writeText(`{text}`)</script>", unsafe_allow_html=True),
                    )
                with bcol2:
                    if not verified:
                        if st.button("✅ 标记已核查", key=f"verify_{idx}"):
                            st.session_state["verify_message_index"] = idx
                            st.session_state["show_verify_modal"] = True
                            st.rerun()

    # 底部提示
    st.markdown("---")
    st.caption("💡 提示：所有对话自动保存到本地项目文件，可随时回溯。关键信息请务必交叉验证。")
