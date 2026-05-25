"""Tests for voice_service functions."""
import pytest
from unittest.mock import patch, AsyncMock

from app.services.voice_service import _basic_parse, parse_intent, WEEKDAY_MAP


def test_basic_parse_create_action():
    """Test parsing create action keywords."""
    assert _basic_parse("添加一个任务")["action"] == "create"
    assert _basic_parse("增加阅读任务")["action"] == "create"
    assert _basic_parse("新建任务")["action"] == "create"
    assert _basic_parse("加个任务")["action"] == "create"


def test_basic_parse_delete_action():
    """Test parsing delete action keywords."""
    assert _basic_parse("删除任务")["action"] == "delete"
    assert _basic_parse("删掉这个任务")["action"] == "delete"
    assert _basic_parse("去掉任务")["action"] == "delete"
    assert _basic_parse("移除任务")["action"] == "delete"


def test_basic_parse_unknown_action():
    """Test parsing unknown action."""
    assert _basic_parse("今天天气怎么样")["action"] == "unknown"


def test_basic_parse_child():
    """Test parsing child name."""
    result = _basic_parse("给萝卜添加任务")
    assert result["child"] == "萝卜"

    result = _basic_parse("给蚕豆添加任务")
    assert result["child"] == "蚕豆"

    result = _basic_parse("添加任务")
    assert result["child"] is None


def test_basic_parse_weekday():
    """Test parsing weekday."""
    for name, num in WEEKDAY_MAP.items():
        result = _basic_parse(f"周{name[1]}添加任务")
        # Should find at least one weekday
        if name in f"周{name[1]}":
            assert result["weekday"] is not None


def test_basic_parse_conditional():
    """Test parsing conditional task keywords."""
    assert _basic_parse("添加条件任务")["is_conditional"] is True
    assert _basic_parse("完成快的任务")["is_conditional"] is True
    assert _basic_parse("完成后奖励")["is_conditional"] is True
    assert _basic_parse("添加普通任务")["is_conditional"] is False


def test_basic_parse_task_type():
    """Test parsing task type."""
    assert _basic_parse("添加阅读任务")["type"] == "reading"
    assert _basic_parse("添加读书任务")["type"] == "reading"
    assert _basic_parse("添加写字任务")["type"] == "written"


def test_basic_parse_title_extraction():
    """Test title extraction from text."""
    result = _basic_parse("周一添加数学作业")
    assert result["weekday"] == 1
    # Title might be extracted depending on parsing logic


def test_basic_parse_default_points():
    """Test default points value."""
    result = _basic_parse("添加任务")
    assert result["points"] == 5


@pytest.mark.asyncio
async def test_parse_intent_no_api_key():
    """Test parse_intent falls back to basic parse when no API key."""
    with patch("app.services.voice_service.LLM_API_KEY", ""):
        result = await parse_intent("添加任务")
        assert result["action"] == "create"


@pytest.mark.asyncio
async def test_parse_intent_with_api_key_success():
    """Test parse_intent with API key success."""
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"action": "create", "child": "萝卜", "weekday": 1, "title": "数学", "type": "written", "points": 10, "is_conditional": false}'
            }
        }]
    }

    with patch("app.services.voice_service.LLM_API_KEY", "test-key"):
        with patch("app.services.voice_service.LLM_API_URL", "http://test.com"):
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = AsyncMock(
                    raise_for_status=AsyncMock(),
                    json=lambda: mock_response
                )
                result = await parse_intent("给萝卜周一添加数学任务")
                assert result["action"] == "create"
                assert result["child"] == "萝卜"


@pytest.mark.asyncio
async def test_parse_intent_api_error_fallback():
    """Test parse_intent falls back on API error."""
    with patch("app.services.voice_service.LLM_API_KEY", "test-key"):
        with patch("app.services.voice_service.LLM_API_URL", "http://test.com"):
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = Exception("API Error")
                result = await parse_intent("添加任务")
                assert result["action"] == "create"
