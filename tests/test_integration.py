import pytest
from fastapi.testclient import TestClient
from aiohttp import web
from aiohttp.test_utils import TestServer, make_mocked_request
from web_mcp import app as web_mcp_app
from rmf import RemoteMCPFetcher
import aiohttp
import asyncio
from unittest.mock import patch, MagicMock

# テスト用の設定ファイルパス
TEST_CONFIG = """
remote_mcps:
  - name: "Text Processing MCP"
    base_url: "http://localhost:8003"
    namespace: "text"
    timeout: 5
    retry:
      max_attempts: 2
      initial_delay: 1
      max_delay: 3

logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "rmf_test.log"

server:
  sse_enabled: true
  sse_retry_timeout: 1000
  max_concurrent_requests: 5
"""

class TestIntegration:
    """RMFとWeb MCPの統合テスト"""

    @pytest.fixture
    def web_mcp_client(self):
        """Web MCPのテストクライアントを作成"""
        return TestClient(web_mcp_app)

    @pytest.fixture
    def config_file(self, tmp_path):
        """テスト用の設定ファイルを作成"""
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(TEST_CONFIG)
        return str(config_path)

    @pytest.fixture
    def rmf(self, config_file):
        """RMFインスタンスを作成"""
        return RemoteMCPFetcher(config_file)

    @pytest.mark.asyncio
    async def test_fetch_tools_integration(self, rmf, web_mcp_client):
        """ツール一覧取得の統合テスト"""
        # Web MCPのレスポンスを直接テスト
        response = web_mcp_client.get("/tools/list")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        tools = data["tools"]
        assert len(tools) > 0
        assert tools[0]["name"] == "to_uppercase"

    @pytest.mark.asyncio
    async def test_uppercase_conversion_integration(self, rmf, web_mcp_client):
        """大文字変換機能の統合テスト"""
        test_cases = [
            ("hello world", "HELLO WORLD"),
            ("Python Integration", "PYTHON INTEGRATION"),
            ("RMF test", "RMF TEST")
        ]

        for input_text, expected in test_cases:
            response = web_mcp_client.post(
                "/tools/call",
                json={
                    "tool": "to_uppercase",
                    "arguments": {"text": input_text}
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["content"][0]["text"] == expected

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, rmf, web_mcp_client):
        """エラーハンドリングの統合テスト"""
        response = web_mcp_client.post(
            "/tools/call",
            json={
                "tool": "non_existent_tool",
                "arguments": {"text": "test"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unknown tool" in data["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_retry_mechanism_integration(self, rmf, web_mcp_client):
        """リトライ機能の統合テスト"""
        response = web_mcp_client.post(
            "/tools/call",
            json={
                "tool": "to_uppercase",
                "arguments": {"text": "retry test"}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"][0]["text"] == "RETRY TEST"

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 