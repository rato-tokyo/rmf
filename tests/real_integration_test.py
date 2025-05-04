"""実際のサーバーを使った統合テスト

このテストはモックを使用せず、実際に起動しているRMFサーバーとMCPサーバーに
対して統合テストを実行します。
"""

import pytest
import asyncio
import aiohttp
import logging
import time
import sys
import os

# テスト前の準備（サーバーの起動確認）
@pytest.fixture(scope="module")
async def ensure_servers_running():
    """サーバーが起動していることを確認する"""
    rmf_url = "http://127.0.0.1:8004"
    mcp_url = "http://127.0.0.1:8003"
    
    # サーバー起動チェック（最大30秒間）
    servers_ready = False
    for _ in range(10):
        try:
            async with aiohttp.ClientSession() as session:
                # RMFサーバーの確認
                async with session.get(f"{rmf_url}/health", timeout=1) as resp:
                    rmf_ok = resp.status == 200
                
                # MCPサーバーの確認
                async with session.get(f"{mcp_url}/tools/list", timeout=1) as resp:
                    mcp_ok = resp.status == 200
                
                if rmf_ok and mcp_ok:
                    servers_ready = True
                    break
        except Exception as e:
            print(f"サーバー接続確認中... {str(e)}")
        
        # 少し待ってから再試行
        await asyncio.sleep(3)
    
    if not servers_ready:
        pytest.skip("RMFサーバーまたはMCPサーバーが実行されていません")
    
    return {"rmf_url": rmf_url, "mcp_url": mcp_url}

class TestRealIntegration:
    """実際のサーバーを使った統合テスト"""

    @pytest.mark.asyncio
    async def test_tools_list(self, ensure_servers_running):
        """ツール一覧取得テスト"""
        rmf_url = ensure_servers_running["rmf_url"]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{rmf_url}/tools/list") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert "tools" in data
                
                # 少なくとも1つのツールがあることを確認
                tools = data["tools"]
                assert len(tools) > 0
                
                # to_uppercaseツールが含まれているか確認
                tool_names = [tool["name"] for tool in tools]
                assert "to_uppercase" in tool_names
    
    @pytest.mark.asyncio
    async def test_call_tool(self, ensure_servers_running):
        """ツール呼び出しテスト"""
        rmf_url = ensure_servers_running["rmf_url"]
        test_text = "hello world"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{rmf_url}/tools/call", 
                json={
                    "tool": "to_uppercase",
                    "arguments": {"text": test_text}
                }
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                assert "content" in data
                
                # 結果の検証
                content = data["content"]
                assert len(content) > 0
                assert content[0]["type"] == "text"
                assert content[0]["text"] == test_text.upper()
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self, ensure_servers_running):
        """存在しないツール呼び出しテスト"""
        rmf_url = ensure_servers_running["rmf_url"]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{rmf_url}/tools/call", 
                json={
                    "tool": "non_existent_tool",
                    "arguments": {"text": "test"}
                }
            ) as resp:
                # テスト環境では200 OKが返り、Unknown toolメッセージが含まれる
                assert resp.status == 200
                data = await resp.json()
                assert "content" in data
                content = data["content"]
                assert len(content) > 0
                assert content[0]["type"] == "text"
                assert "Unknown tool" in content[0]["text"]
    
    @pytest.mark.asyncio
    async def test_multiple_requests(self, ensure_servers_running):
        """複数リクエストの並行処理テスト"""
        rmf_url = ensure_servers_running["rmf_url"]
        
        async def call_uppercase(text):
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{rmf_url}/tools/call", 
                    json={
                        "tool": "to_uppercase",
                        "arguments": {"text": text}
                    }
                ) as resp:
                    data = await resp.json()
                    return data["content"][0]["text"]
        
        # 5つの並行リクエストを送信
        texts = ["test1", "test2", "test3", "test4", "test5"]
        tasks = [call_uppercase(text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        # 結果を検証
        for i, result in enumerate(results):
            assert result == texts[i].upper()

if __name__ == "__main__":
    # コマンドラインから直接実行された場合
    pytest.main(["-v", __file__]) 