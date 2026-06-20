"""
大语言模型API客户端模块
支持OpenAI格式的API接口（base_url + api_key）
兼容DeepSeek、Kimi等国内大模型服务
"""
import json
import os
import requests
from config import CONFIG_FILE


def load_api_config():
    """
    加载API配置
    如果配置文件不存在，返回空配置

    Returns:
        dict: 包含base_url、api_key、model的配置字典
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"base_url": "", "api_key": "", "model": "deepseek-chat"}


def save_api_config(base_url, api_key, model):
    """
    保存API配置到本地文件

    Args:
        base_url (str): API基础地址
        api_key (str): API密钥
        model (str): 模型名称

    Returns:
        bool: 保存是否成功
    """
    config = {"base_url": base_url, "api_key": api_key, "model": model}
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


def chat_completion(messages, stream=True):
    """
    调用大模型API进行对话

    Args:
        messages (list): 消息列表，每个元素为{"role": "user"/"assistant", "content": "..."}
        stream (bool): 是否使用流式输出，默认True

    Returns:
        generator or str: 流式输出时返回生成器，非流式返回完整字符串
        出错时返回包含错误信息的字符串
    """
    config = load_api_config()
    base_url = config.get("base_url", "").rstrip("/")
    api_key = config.get("api_key", "")
    model = config.get("model", "deepseek-chat")

    if not base_url or not api_key:
        return "错误：请先配置API地址和密钥。在左侧边栏的「API设置」中填写。"

    # 自动补全/v1/chat/completions路径
    if "/v1/chat/completions" not in base_url:
        api_url = f"{base_url}/v1/chat/completions"
    else:
        api_url = base_url

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "temperature": 0.7,
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, stream=stream, timeout=120)
        response.raise_for_status()

        if stream:
            def stream_generator():
                for line in response.iter_lines():
                    if not line:
                        continue
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"]
                            if "content" in delta and delta["content"]:
                                yield delta["content"]
                        except Exception:
                            continue
            return stream_generator()
        else:
            result = response.json()
            return result["choices"][0]["message"]["content"]

    except requests.exceptions.ConnectionError:
        return "错误：无法连接到API服务器，请检查网络或base_url是否正确。"
    except requests.exceptions.Timeout:
        return "错误：API请求超时，请稍后重试。"
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "未知"
        return f"错误：API返回HTTP {status}，请检查api_key是否有效。"
    except Exception as e:
        return f"错误：API调用失败 - {str(e)}"
