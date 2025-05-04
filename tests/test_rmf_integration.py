"""RMFの統合テスト"""

import pytest
import asyncio
import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestServer
from rmf import RemoteMCPFetcher
from rmf.exceptions import *
import tempfile
import os
import yaml
from typing import Dict, Any, List
import logging

# テスト用のMCPサーバー
async def mock_mcp_server():
    app = web.Application()
    
    # テスト用の状態管理
    app["failure_count"] = 0
    app["should_timeout"] = False
    app["should_fail"] = False
    
    async def tools_list(request):
        # リトライテスト用
        if app.get("should_fail", False):
            # 最初の2回は失敗、3回目で成功
            if app["failure_count"] < 2:
                app["failure_count"] += 1
                raise web.HTTPServiceUnavailable()
        
        # タイムアウトテスト用
        if app.get("should_timeout", False):
            await asyncio.sleep(0.5)
        
        return web.json_response({
            "tools": [
                {
                    "name": "to_uppercase",
                    "description": "テキストを大文字に変換するツール",
                    "parameters": {
                        "text": {
                            "type": "string",
                            "description": "変換したいテキスト"
                        }
                    }
                }
            ]
        })
    
    async def tools_call(request):
        data = await request.json()
        tool = data.get("tool")
        args = data.get("arguments", {})
        
        if tool == "to_uppercase":
            text = args.get("text", "")
            return web.json_response({
                "content": [
                    {
                        "type": "text",
                        "text": text.upper()
                    }
                ]
            })
        else:
            return web.Response(
                status=404,
                text=f"Unknown tool: {tool}"
            )
    
    app.router.add_get("/tools/list", tools_list)
    app.router.add_post("/tools/call", tools_call)
    
    # テスト用のアクセサメソッド
    app["set_timeout_mode"] = lambda mode: app.update({"should_timeout": mode})
    app["set_failure_mode"] = lambda mode: app.update({"should_fail": mode})
    app["get_failure_count"] = lambda: app["failure_count"]
    app["reset_failure_count"] = lambda: app.update({"failure_count": 0})
    
    return app

class TestRMFIntegration:
    """RMFの統合テスト"""
    
    @pytest.fixture
    async def mcp_server(self, aiohttp_server):
        """MCPサーバーのセットアップ"""
        app = await mock_mcp_server()
        server = await aiohttp_server(app)
        yield server
        await server.close()
    
    @pytest.fixture
    def config_file(self, mcp_server, tmp_path):
        """テスト用の設定ファイルを作成"""
        config = {
            "remote_mcps": [
                {
                    "name": "Test MCP",
                    "base_url": f"http://localhost:{mcp_server.port}",
                    "namespace": "test",
                    "timeout": 5,
                    "retry": {
                        "max_attempts": 3,
                        "initial_delay": 0.1,
                        "max_delay": 0.3
                    }
                }
            ],
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": str(tmp_path / "test.log")
            }
        }
        
        config_path = tmp_path / "test_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        
        return str(config_path)
    
    @pytest.fixture
    def rmf(self, config_file):
        """RMFインスタンスを作成"""
        return RemoteMCPFetcher(config_file)

    @pytest.fixture
    def caplog(self, caplog):
        """ログキャプチャの設定"""
        caplog.set_level(logging.INFO)
        return caplog
    
    def _check_log_context(self, records: List[logging.LogRecord], key: str) -> bool:
        """ログレコードのコンテキストに特定のキーが含まれているか確認"""
        for record in records:
            if hasattr(record, 'rmf_context') and isinstance(record.rmf_context, dict):
                if key in record.rmf_context:
                    return True
        return False
    
    @pytest.mark.asyncio
    async def test_fetch_tools_integration(self, rmf, mcp_server, caplog):
        """ツール一覧取得の統合テスト"""
        tools = await rmf._fetch_tools_from_remote(rmf.remote_mcps[0])
        assert len(tools) == 1
        assert tools[0]["name"] == "to_uppercase"
        
        # ログの検証
        assert "ツール一覧の取得開始" in caplog.text
        assert "ツール一覧の取得成功" in caplog.text
        assert self._check_log_context(caplog.records, 'trace_id')
    
    @pytest.mark.asyncio
    async def test_tool_call_integration(self, rmf, mcp_server, caplog):
        """ツール呼び出しの統合テスト"""
        result = await rmf._call_remote_tool(
            "to_uppercase",
            {"text": "hello world"}
        )
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "HELLO WORLD"
        
        # ログの検証
        assert "ツール呼び出し開始" in caplog.text
        assert "ツール呼び出し成功" in caplog.text
        assert self._check_log_context(caplog.records, 'trace_id')
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, rmf, mcp_server, caplog):
        """エラーハンドリングの統合テスト"""
        with pytest.raises(ToolError) as exc_info:
            await rmf._call_remote_tool(
                "non_existent_tool",
                {"text": "test"}
            )
        assert "404" in str(exc_info.value)
        
        # ログの検証
        assert "ツール呼び出し失敗" in caplog.text or "エラー" in caplog.text
        assert self._check_log_context(caplog.records, 'status_code')
    
    @pytest.mark.asyncio
    async def test_timeout_handling_integration(self, rmf, mcp_server, caplog):
        """タイムアウト処理の統合テスト"""
        rmf.remote_mcps[0].timeout = 0.1
        mcp_server.app["set_timeout_mode"](True)
        
        with pytest.raises(TimeoutError):
            await rmf._fetch_tools_from_remote(rmf.remote_mcps[0])
        
        # ログの検証
        mcp_server.app["set_timeout_mode"](False)  # リセット
        assert "タイムアウト" in caplog.text or "エラー" in caplog.text
    
    @pytest.mark.asyncio
    async def test_connection_error_integration(self, rmf, caplog):
        """接続エラーの統合テスト"""
        rmf.remote_mcps[0].base_url = "http://non-existent-server:12345"
        
        with pytest.raises(ConnectionError):
            await rmf._fetch_tools_from_remote(rmf.remote_mcps[0])
        
        # ログの検証
        assert "エラー" in caplog.text
        assert self._check_log_context(caplog.records, 'exception_type')
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_integration(self, rmf, mcp_server, caplog):
        """リトライ機能の統合テスト"""
        mcp_server.app["reset_failure_count"]()
        mcp_server.app["set_failure_mode"](True)
        
        tools = await rmf._fetch_tools_from_remote(rmf.remote_mcps[0])
        
        # テストの検証
        assert len(tools) == 1
        assert tools[0]["name"] == "to_uppercase"
        assert mcp_server.app["get_failure_count"]() == 2  # 2回失敗してから成功
        
        # 後始末
        mcp_server.app["set_failure_mode"](False)
        
        # ログの検証
        error_count = sum(1 for record in caplog.records if "エラー" in record.message)
        assert error_count >= 2
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_integration(self, rmf, mcp_server):
        """並行リクエストの統合テスト"""
        tasks = []
        for i in range(5):
            tasks.append(
                rmf._call_remote_tool(
                    "to_uppercase",
                    {"text": f"test{i}"}
                )
            )
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(len(r) == 1 for r in results)
        assert all(r[0]["type"] == "text" for r in results)
        assert all(r[0]["text"].isupper() for r in results)

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 