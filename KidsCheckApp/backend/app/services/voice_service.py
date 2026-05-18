import json
import httpx

from app.config import LLM_API_KEY, LLM_API_URL, LLM_MODEL

WEEKDAY_MAP = {
    "周一": 1, "周二": 2, "周三": 3, "周四": 4, "周五": 5, "周六": 6, "周日": 7,
    "星期一": 1, "星期二": 2, "星期三": 3, "星期四": 4, "星期五": 5, "星期六": 6, "星期日": 7,
    "礼拜一": 1, "礼拜二": 2, "礼拜三": 3, "礼拜四": 4, "礼拜五": 5, "礼拜六": 6, "礼拜日": 7,
}

SYSTEM_PROMPT = """你是一个任务管理助手，负责从用户的语音指令中提取结构化信息。
用户可能是家长，想要管理孩子的学习任务。

你需要输出JSON格式：
{
  "action": "create" | "delete" | "update",
  "child": "萝卜" | "蚕豆" | null,
  "weekday": 1-7 或 null (1=周一, 7=周日),
  "title": "任务名称" 或 null,
  "type": "written" | "reading" | null,
  "points": 数字 或 null,
  "is_conditional": true | false
}

如果用户提到"条件任务"或"完成快"相关，is_conditional 为 true。
如果无法解析，返回 {"action": "unknown"}"""


async def parse_intent(text: str) -> dict:
    """Call LLM to parse voice text into structured intent."""
    if not LLM_API_KEY:
        # Fallback: basic keyword extraction
        return _basic_parse(text)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                LLM_API_URL,
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": text},
                    ],
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception:
        return _basic_parse(text)


def _basic_parse(text: str) -> dict:
    """Fallback keyword-based parsing."""
    action = "unknown"
    if any(w in text for w in ["添加", "增加", "新建", "加个"]):
        action = "create"
    elif any(w in text for w in ["删除", "删掉", "去掉", "移除"]):
        action = "delete"

    child = None
    if "萝卜" in text:
        child = "萝卜"
    elif "蚕豆" in text:
        child = "蚕豆"

    weekday = None
    for key, val in WEEKDAY_MAP.items():
        if key in text:
            weekday = val
            break

    title = None
    # Extract text after weekday mention
    for key in WEEKDAY_MAP:
        if key in text:
            parts = text.split(key, 1)
            if len(parts) > 1:
                rest = parts[1].strip()
                # Remove common verbs
                for verb in ["添加", "加", "删除", "删掉", "增加"]:
                    rest = rest.replace(verb, "").strip()
                # Remove "任务" suffix
                rest = rest.replace("任务", "").strip()
                if rest:
                    title = rest
            break

    is_conditional = any(w in text for w in ["条件", "完成快", "完成后"])

    task_type = "written"
    if any(w in text for w in ["阅读", "读书"]):
        task_type = "reading"

    return {
        "action": action,
        "child": child,
        "weekday": weekday,
        "title": title,
        "type": task_type,
        "points": 5,
        "is_conditional": is_conditional,
    }
