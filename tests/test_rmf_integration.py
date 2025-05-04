"""RMF統合テスト"""

import os
import json
import pytest
import aiohttp
import asyncio
from typing import Dict, Any
from aiohttp import web
from rmf import RMF, RMFError, TimeoutError, ConnectionError, ToolError, LogContext

# テスト用の設定
TEST_CONFIG = {
    "remote_mcps": [
        {
            "name": "Test MCP",
            "base_url": "http://localhost:8003",
            "namespace": "test",
            "timeout": 5,
            "retry": {
                "max_attempts": 3,
                "initial_delay": 0.1,
                "max_delay": 1.0
            },
            "headers": None
        }
    ]
}

# モックサーバーのルート
async def handle_tools_list(request):
    """ツール一覧エンドポイントのハンドラ"""
    return web.json_response([
        {
            "name": "test_tool",
            "description": "テスト用ツール",
            "parameters": {
                "param1": "string",
                "param2": "integer"
            }
        }
    ])

async def handle_tools_call(request):
    """ツール呼び出しエンドポイントのハンドラ"""
    data = await request.json()
    return web.json_response({
        "result": f"Called {data['tool']} with {data['arguments']}"
    })

async def handle_service_unavailable(request):
    """503エラーを返すハンドラ"""
    raise web.HTTPServiceUnavailable()

async def handle_timeout(request):
    """タイムアウトをシミュレートするハンドラ"""
    await asyncio.sleep(2)  # 2秒待機
    return web.json_response({"status": "timeout"})

@pytest.fixture
async def mock_server():
    """モックサーバーのフィクスチャ"""
    app = web.Application()
    app.router.add_get('/tools/list', handle_tools_list)
    app.router.add_post('/tools/call', handle_tools_call)
    app.router.add_get('/error/503', handle_service_unavailable)
    app.router.add_get('/timeout/tools/list', handle_timeout)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8003)
    await site.start()
    
    yield site
    
    await runner.cleanup()

@pytest.fixture
async def rmf_client():
    """RMFクライアントのフィクスチャ"""
    client = RMF(TEST_CONFIG)
    await client.setup()
    yield client
    await client.cleanup()

@pytest.mark.asyncio
async def test_get_tools_success(mock_server, rmf_client):
    """ツール一覧取得の成功テスト"""
    with LogContext(test_name="test_get_tools_success"):
        tools = await rmf_client.get_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

@pytest.mark.asyncio
async def test_call_tool_success(mock_server, rmf_client):
    """ツール呼び出しの成功テスト"""
    with LogContext(test_name="test_call_tool_success"):
        result = await rmf_client.call_tool(
            "test_tool",
            {"param1": "value1", "param2": 42}
        )
        assert "Called test_tool" in result["result"]

@pytest.mark.asyncio
async def test_retry_mechanism_integration(mock_server, rmf_client):
    """リトライメカニズムの統合テスト"""
    with LogContext(test_name="test_retry_mechanism_integration"):
        with pytest.raises(RMFError):
            await rmf_client._fetch_tools_from_remote({
                "name": "Error Test MCP",
                "base_url": "http://localhost:8003/error",
                "timeout": 1,
                "headers": None
            })

@pytest.mark.asyncio
async def test_timeout_handling(mock_server, rmf_client):
    """タイムアウト処理のテスト"""
    with LogContext(test_name="test_timeout_handling"):
        with pytest.raises(TimeoutError):
            await rmf_client._fetch_tools_from_remote({
                "name": "Timeout Test MCP",
                "base_url": "http://localhost:8003/timeout",  # タイムアウトをシミュレートするエンドポイント
                "timeout": 1,
                "headers": None
            })

@pytest.mark.asyncio
async def test_connection_error_handling(mock_server, rmf_client):
    """接続エラー処理のテスト"""
    with LogContext(test_name="test_connection_error_handling"):
        with pytest.raises(ConnectionError):
            await rmf_client._fetch_tools_from_remote({
                "name": "Connection Error Test MCP",
                "base_url": "http://non-existent-host.invalid",  # 存在しないホスト
                "timeout": 1,
                "headers": None
            })

@pytest.mark.asyncio
async def test_tool_error_handling(mock_server, rmf_client):
    """ツールエラー処理のテスト"""
    with LogContext(test_name="test_tool_error_handling"):
        with pytest.raises(ToolError):
            await rmf_client._call_remote_tool(
                {
                    "name": "Error Test MCP",
                    "base_url": "http://localhost:8003/error",
                    "timeout": 1,
                    "headers": None
                },
                "invalid_tool",
                {}
            )

@pytest.mark.asyncio
async def test_mcp_selection(mock_server, rmf_client):
    """MCP選択のテスト"""
    with LogContext(test_name="test_mcp_selection"):
        # 存在するMCP名を指定
        tools = await rmf_client.get_tools("Test MCP")
        assert len(tools) == 1
        
        # 存在しないMCP名を指定
        with pytest.raises(ValueError):
            await rmf_client.call_tool(
                "test_tool",
                {"param1": "value1"},
                mcp_name="Non-existent MCP"
            )

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 