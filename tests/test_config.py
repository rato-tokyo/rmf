"""設定管理の統合テスト"""

import os
import pytest
import json
import logging
import tempfile
from pathlib import Path
from rmf.config import Config
from rmf.errors import ConfigError
from tests.utils import test_env, log_test_env, temp_log_file


# 各テストの前後で環境変数をクリア
@pytest.fixture(autouse=True)
def clean_environment():
    """各テストの前後で環境変数をクリア"""
    # テスト前に環境変数をクリア
    original_env = {k: v for k, v in os.environ.items() if not k.startswith('RMF_')}
    
    # RMF_関連の環境変数をクリア
    for key in list(os.environ.keys()):
        if key.startswith('RMF_'):
            del os.environ[key]
    
    yield
    
    # テスト後に環境変数を復元
    os.environ.clear()
    os.environ.update(original_env)


def test_default_config():
    """デフォルト設定のテスト"""
    config = Config()
    
    # デフォルト値の検証
    assert config.remote_mcps[0]['base_url'] == 'http://localhost:8003'
    assert config.remote_mcps[0]['timeout'] == 5
    assert config.remote_mcps[0]['retry']['max_attempts'] == 3
    
    assert config.logging['level'] == 'INFO'
    assert config.logging['format'] == 'json'
    assert config.logging['file'] == 'rmf.log'
    
    assert config.server['sse_enabled'] is True
    assert config.server['sse_retry_timeout'] == 3000
    assert config.server['max_concurrent_requests'] == 10


def test_custom_config():
    """カスタム設定のテスト"""
    # テスト用の環境変数を設定
    os.environ['RMF_MCP_BASE_URL'] = 'http://test-mcp:8080'
    os.environ['RMF_MCP_TIMEOUT'] = '10'
    os.environ['RMF_LOG_LEVEL'] = 'DEBUG'
    os.environ['RMF_SERVER_MAX_CONCURRENT_REQUESTS'] = '20'
    
    config = Config()
    
    # カスタム値の検証
    assert config.remote_mcps[0]['base_url'] == 'http://test-mcp:8080'
    assert config.remote_mcps[0]['timeout'] == 10
    assert config.logging['level'] == 'DEBUG'
    assert config.server['max_concurrent_requests'] == 20


def test_test_environment():
    """テスト環境の設定テスト"""
    os.environ['RMF_ENV'] = 'test'
    config = Config()
    
    assert config.logging['level'] == 'DEBUG'
    assert config.logging['file'] == 'rmf_test.log'
    assert config.server['sse_retry_timeout'] == 1000
    assert config.server['max_concurrent_requests'] == 5


def test_development_environment():
    """開発環境の設定テスト"""
    os.environ['RMF_ENV'] = 'development'
    config = Config()
    
    assert config.logging['level'] == 'DEBUG'
    assert config.logging['file'] == 'rmf_dev.log'
    assert config.server['sse_retry_timeout'] == 1500
    assert config.server['max_concurrent_requests'] == 3


def test_invalid_values():
    """無効な値のテスト"""
    os.environ['RMF_MCP_TIMEOUT'] = 'invalid'
    
    with pytest.raises(ConfigError) as exc_info:
        Config()
    
    assert exc_info.value.error_code == 'CFG'
    assert 'Invalid integer value for RMF_MCP_TIMEOUT' in str(exc_info.value)
    assert exc_info.value.details['parameter'] == 'RMF_MCP_TIMEOUT'
    assert exc_info.value.details['value'] == 'invalid'
    assert exc_info.value.details['expected_type'] == 'integer'


def test_get_config():
    """get_config()メソッドのテスト"""
    config = Config()
    full_config = config.get_config()
    
    assert 'remote_mcps' in full_config
    assert 'logging' in full_config
    assert 'server' in full_config
    assert isinstance(full_config['remote_mcps'], list)
    assert isinstance(full_config['logging'], dict)
    assert isinstance(full_config['server'], dict)


def test_logging_output(log_test_env):
    """ロギング出力のテスト"""
    os.environ['RMF_ENV'] = 'test'
    config = Config()
    
    # ログファイルが作成されていることを確認
    assert log_test_env.log_file_path.exists()
    
    # ログエントリを取得
    log_entries = log_test_env.get_log_entries()
    
    # 空のファイルでないことを確認
    assert log_entries, "ログファイルが空です"
    
    # 設定読み込み成功のログを確認
    success_logs = log_test_env.find_log_entries(level="INFO", message_contains="Configuration loaded successfully")
    assert success_logs, "設定読み込み成功のログが見つかりません"
    
    success_log = success_logs[0]
    assert success_log['details']['environment'] == 'test'
    
    # 環境設定適用のログを確認
    env_logs = log_test_env.find_log_entries(level="DEBUG", message_contains="Test environment configuration applied")
    assert env_logs, "環境設定適用のログが見つかりません"
    
    env_log = env_logs[0]
    assert env_log['details']['environment'] == 'test'


def test_error_logging(log_test_env):
    """エラーログのテスト"""
    # まず正常にロガーを初期化するための設定
    os.environ['RMF_ENV'] = 'production'
    config = Config()
    
    # 次にエラーを起こすための環境変数設定
    os.environ['RMF_MCP_TIMEOUT'] = 'invalid'
    
    # エラーが発生することを確認
    with pytest.raises(ConfigError):
        Config()
    
    # ログファイルが作成されていることを確認
    assert log_test_env.log_file_path.exists()
    
    # ログエントリを取得
    log_entries = log_test_env.get_log_entries()
    
    # 空のファイルでないことを確認
    assert log_entries, "ログファイルが空です"
    
    # エラーログを検索
    error_logs = log_test_env.find_log_entries(level="ERROR", message_contains="Invalid integer value for RMF_MCP_TIMEOUT")
    assert error_logs, "エラーログが見つかりません"
    
    # 最後のエラーログを取得
    error_log = error_logs[-1]
    
    # エラーログの内容を確認
    assert 'Invalid integer value for RMF_MCP_TIMEOUT' in error_log['message']
    assert 'error' in error_log
    assert error_log['error']['type'] == 'ConfigError' 