"""
项目管理模块
负责项目的创建、加载、保存和删除
所有数据以JSON格式本地存储
"""
import json
import os
import uuid
from datetime import datetime
from config import PROJECTS_DIR, ensure_directories


def get_all_projects():
    """
    获取所有项目列表

    Returns:
        list: 项目基本信息列表，每个元素包含id、name、topic、updated_at
    """
    ensure_directories()
    projects = []
    for filename in os.listdir(PROJECTS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(PROJECTS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                projects.append({
                    "id": data.get("id", filename.replace(".json", "")),
                    "name": data.get("name", "未命名项目"),
                    "topic": data.get("topic", ""),
                    "updated_at": data.get("updated_at", ""),
                })
            except Exception:
                continue
    # 按更新时间倒序排列
    projects.sort(key=lambda x: x["updated_at"], reverse=True)
    return projects


def create_project(name, topic, keywords, core_papers):
    """
    创建新项目

    Args:
        name (str): 项目名称
        topic (str): 研究主题
        keywords (str): 核心关键词
        core_papers (str): 已知核心文献（1-2篇）

    Returns:
        dict: 新创建的项目数据
    """
    ensure_directories()
    project_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    project = {
        "id": project_id,
        "name": name,
        "topic": topic,
        "keywords": keywords,
        "core_papers": core_papers,
        "created_at": now,
        "updated_at": now,
        "current_stage": "literature",
        "history": [],
        "verification_notes": {},
    }
    save_project(project)
    return project


def load_project(project_id):
    """
    加载指定项目

    Args:
        project_id (str): 项目ID

    Returns:
        dict or None: 项目数据，不存在则返回None
    """
    filepath = os.path.join(PROJECTS_DIR, f"{project_id}.json")
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_project(project):
    """
    保存项目数据到本地JSON文件

    Args:
        project (dict): 项目数据字典

    Returns:
        bool: 保存是否成功
    """
    ensure_directories()
    filepath = os.path.join(PROJECTS_DIR, f"{project['id']}.json")
    try:
        project["updated_at"] = datetime.now().isoformat()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存项目失败: {e}")
        return False


def delete_project(project_id):
    """
    删除项目

    Args:
        project_id (str): 项目ID

    Returns:
        bool: 删除是否成功
    """
    filepath = os.path.join(PROJECTS_DIR, f"{project_id}.json")
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception:
            return False
    return False


def add_chat_message(project_id, role, content, stage):
    """
    向项目历史中添加一条对话记录

    Args:
        project_id (str): 项目ID
        role (str): 'user' 或 'assistant'
        content (str): 消息内容
        stage (str): 当前阶段ID

    Returns:
        bool: 添加是否成功
    """
    project = load_project(project_id)
    if not project:
        return False
    message = {
        "role": role,
        "content": content,
        "stage": stage,
        "timestamp": datetime.now().isoformat(),
        "verified": False,
    }
    project["history"].append(message)
    return save_project(project)


def mark_message_verified(project_id, message_index, note=""):
    """
    标记某条消息为已核查

    Args:
        project_id (str): 项目ID
        message_index (int): 消息在历史记录中的索引
        note (str): 核查备注

    Returns:
        bool: 操作是否成功
    """
    project = load_project(project_id)
    if not project or message_index >= len(project["history"]):
        return False
    project["history"][message_index]["verified"] = True
    project["verification_notes"][str(message_index)] = note
    return save_project(project)
