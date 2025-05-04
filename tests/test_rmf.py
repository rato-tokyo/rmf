import os
import sys
import json
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from aioresponses import aioresponses
from aiohttp import web, ClientTimeout
from aiohttp.test_utils import make_mocked_request

# プロジェクトルートをPYTHONPATHに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from rmf import RemoteMCPFetcher, RemoteMCPConfig, RetryConfig

# 定数定義
TEST_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config_test.yaml")
TEST_TOOLS = {
    "tools": [
        {
            "name": "test_tool1",
            "description": "Test tool 1",
            "parameters": {}
        },
        {
            "name": "test_tool2",
            "description": "Test tool 2",
            "parameters": {}
        }
    ]
}

class TestRemoteMCPFetcher:
    """Remote MCP Fetcherのテストスイート"""

    @pytest.fixture
    def rmf(self):
        """RMFインスタンスを作成"""
        return RemoteMCPFetcher(TEST_CONFIG_PATH)

    @pytest.fixture
    def mock_aiohttp(self):
        """aiohttpのモックを作成"""
        with aioresponses() as m:
            yield m

    @pytest.mark.asyncio
    async def test_fetch_tools_success(self, rmf, mock_aiohttp):
        """ツール一覧の取得テスト（成功）"""
        # モックの設定
        for mcp in rmf.remote_mcps:
            mock_aiohttp.get(
                f"{mcp.base_url}/tools/list",
                payload=TEST_TOOLS,
                status=200
            )

        # テスト実行
        for mcp in rmf.remote_mcps:
            tools = await rmf._fetch_tools_from_remote(mcp)
            assert len(tools) == len(TEST_TOOLS["tools"])
            
            # 名前空間の確認
            for tool in tools:
                assert tool["name"].startswith(f"{mcp.namespace}_")
                assert "_original_name" in tool
                assert "_namespace" in tool

    @pytest.mark.asyncio
    async def test_fetch_tools_failure(self, rmf, mock_aiohttp):
        """ツール一覧の取得テスト（失敗）"""
        # モックの設定
        for mcp in rmf.remote_mcps:
            mock_aiohttp.get(
                f"{mcp.base_url}/tools/list",
                status=500
            )

        # テスト実行
        for mcp in rmf.remote_mcps:
            with pytest.raises(Exception):
                await rmf._fetch_tools_from_remote(mcp)

    @pytest.mark.asyncio
    async def test_call_remote_tool_success(self, rmf, mock_aiohttp):
        """リモートツール呼び出しテスト（成功）"""
        # テストデータ
        tool_name = "test1_tool1"
        arguments = {"arg1": "value1"}
        response_data = {
            "content": [
                {"type": "text", "text": "Test response"}
            ]
        }

        # ツールマップの設定
        rmf.tools_map[tool_name] = {
            "name": tool_name,
            "_original_name": "tool1",
            "_namespace": "test1"
        }
        rmf.namespace_map[tool_name] = rmf.remote_mcps[0]

        # モックの設定
        mock_aiohttp.post(
            f"{rmf.remote_mcps[0].base_url}/tools/call",
            payload=response_data,
            status=200
        )

        # テスト実行
        result = await rmf._call_remote_tool(tool_name, arguments)
        assert result == response_data["content"]

    @pytest.mark.asyncio
    async def test_call_remote_tool_not_found(self, rmf):
        """存在しないツールの呼び出しテスト"""
        result = await rmf._call_remote_tool("non_existent_tool", {})
        assert result[0]["type"] == "text"
        assert "Tool not found" in result[0]["text"]

    @pytest.mark.asyncio
    async def test_sse_notification(self, rmf):
        """SSE通知テスト"""
        # テストデータ
        event = "test_event"
        data = {"test": "data"}

        # モックのSSEクライアント
        mock_client = Mock()
        mock_client.send_str = Mock()
        rmf.sse_clients.add(mock_client)

        # テスト実行
        await rmf._notify_sse_clients(event, data)

        # 検証
        expected_message = json.dumps({"event": event, "data": data})
        mock_client.send_str.assert_called_once_with(expected_message)

    def test_handle_initialize(self, rmf):
        """初期化ハンドラーテスト"""
        request = {"id": 1, "method": "initialize"}
        
        # レスポンス送信のモック
        with patch.object(rmf, 'send_success') as mock_send:
            rmf.handle_initialize(request)
            
            # 検証
            mock_send.assert_called_once()
            response = mock_send.call_args[0][1]
            assert "serverInfo" in response
            assert "capabilities" in response
            assert "protocolVersion" in response

    def test_handle_tools_list(self, rmf):
        """ツール一覧ハンドラーテスト"""
        request = {"id": 1, "method": "tools/list"}
        
        # テストデータ
        test_tool = {
            "name": "test_tool",
            "description": "Test tool"
        }
        rmf.tools_map["test_tool"] = test_tool

        # レスポンス送信のモック
        with patch.object(rmf, 'send_success') as mock_send:
            rmf.handle_tools_list(request)
            
            # 検証
            mock_send.assert_called_once()
            response = mock_send.call_args[0][1]
            assert "tools" in response
            assert len(response["tools"]) == 1
            assert response["tools"][0] == test_tool

    def test_handle_request_unknown_method(self, rmf):
        """未知のメソッドハンドリングテスト"""
        request = {"id": 1, "method": "unknown_method"}
        
        # レスポンス送信のモック
        with patch.object(rmf, 'send_error') as mock_send:
            rmf.handle_request(request)
            
            # 検証
            mock_send.assert_called_once_with(1, -32601, "Method not found")

    def test_config_loading(self, rmf):
        """設定ファイル読み込みテスト"""
        assert len(rmf.remote_mcps) == 2
        assert rmf.config["server"]["sse_enabled"] is True
        assert rmf.config["logging"]["level"] == "DEBUG"

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, rmf, mock_aiohttp):
        """リトライ機能テスト"""
        mcp = rmf.remote_mcps[0]
        
        # 最初の2回は失敗、3回目は成功するように設定
        mock_aiohttp.get(
            f"{mcp.base_url}/tools/list",
            status=500,
            repeat=False
        )
        mock_aiohttp.get(
            f"{mcp.base_url}/tools/list",
            status=500,
            repeat=False
        )
        mock_aiohttp.get(
            f"{mcp.base_url}/tools/list",
            payload={"tools": []},
            status=200
        )

        # テスト実行
        with pytest.raises(Exception):
            await rmf._fetch_tools_from_remote(mcp)

if __name__ == '__main__':
    pytest.main(['-v', __file__]) 