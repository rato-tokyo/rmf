import pytest
from fastapi.testclient import TestClient
from web_mcp import app

client = TestClient(app)

def test_list_tools():
    """ツール一覧取得のテスト"""
    response = client.get("/tools/list")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    tools = data["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "to_uppercase"

def test_uppercase_conversion():
    """大文字変換機能のテスト"""
    test_cases = [
        ("hello world", "HELLO WORLD"),
        ("Python", "PYTHON"),
        ("OpenAI", "OPENAI"),
        ("", ""),  # 空文字列のテスト
        ("123", "123"),  # 数字のテスト
        ("Hello World!", "HELLO WORLD!")  # 記号を含むテスト
    ]

    for input_text, expected in test_cases:
        response = client.post(
            "/tools/call",
            json={
                "tool": "to_uppercase",
                "arguments": {"text": input_text}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert len(data["content"]) == 1
        assert data["content"][0]["type"] == "text"
        assert data["content"][0]["text"] == expected

def test_unknown_tool():
    """存在しないツールのテスト"""
    response = client.post(
        "/tools/call",
        json={
            "tool": "non_existent_tool",
            "arguments": {"text": "hello"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"][0]["text"] == "Unknown tool"

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 