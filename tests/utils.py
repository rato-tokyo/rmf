"""テスト用ユーティリティ

テストの安定性と再現性を向上させるためのユーティリティクラスとフィクスチャを提供します。
"""

import os
import time
import tempfile
import uuid
import json
import shutil
import pytest
import logging
from pathlib import Path
from contextlib import contextmanager

from rmf.platform import PlatformUtils


class TestFileManager:
    """テスト用ファイル管理クラス
    
    一時ファイルの作成、管理、クリーンアップを行います。
    Windows環境でのファイルロック問題にも対応します。
    """
    
    def __init__(self, prefix="test_", suffix=".log"):
        """初期化
        
        Args:
            prefix: ファイル名のプレフィックス
            suffix: ファイル名のサフィックス
        """
        self.temp_dir = tempfile.mkdtemp()
        self.file_name = f"{prefix}{uuid.uuid4()}{suffix}"
        self.file_path = Path(self.temp_dir) / self.file_name
    
    def setup(self):
        """セットアップ処理
        
        Returns:
            作成された一時ファイルのパス
        """
        # 親ディレクトリが存在しない場合は作成
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 空のファイルを作成
        self.file_path.touch()
        
        return self.file_path
    
    def create_subdirectory(self, subdir_name):
        """サブディレクトリの作成
        
        Args:
            subdir_name: サブディレクトリ名
            
        Returns:
            作成されたサブディレクトリのパス
        """
        subdir_path = Path(self.temp_dir) / subdir_name
        subdir_path.mkdir(parents=True, exist_ok=True)
        return subdir_path
    
    def create_file(self, relative_path, content=""):
        """指定パスにファイルを作成
        
        Args:
            relative_path: 一時ディレクトリからの相対パス
            content: ファイルの内容
            
        Returns:
            作成されたファイルのパス
        """
        file_path = Path(self.temp_dir) / relative_path
        
        # 親ディレクトリが存在しない場合は作成
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ファイルを作成して内容を書き込み
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def cleanup(self):
        """リソースの解放
        
        一時ディレクトリとファイルを削除します。
        """
        # ロガーのハンドラをクリア
        for logger_name in ['rmf', 'root']:
            logger = logging.getLogger(logger_name)
            for handler in list(logger.handlers):
                try:
                    handler.close()
                    logger.removeHandler(handler)
                except Exception:
                    pass
        
        # Windows環境では少し待機してファイルハンドルが確実に解放されるようにする
        if PlatformUtils.is_windows():
            time.sleep(0.2)
        
        # ディレクトリ削除
        PlatformUtils.safe_rmtree(self.temp_dir)
    
    def __enter__(self):
        """コンテキストマネージャのエントリーポイント"""
        return self.setup()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャの終了処理"""
        self.cleanup()


class TestEnvironment:
    """テスト環境管理クラス
    
    テスト環境の設定と復元を行います。
    """
    
    def __init__(self):
        """初期化"""
        self.original_env = os.environ.copy()
        self.file_managers = []
    
    def setup(self):
        """環境のセットアップ"""
        pass
    
    def set_env_vars(self, env_vars):
        """環境変数の設定
        
        Args:
            env_vars: 設定する環境変数の辞書
        """
        for key, value in env_vars.items():
            os.environ[key] = str(value)
    
    def create_temp_file_manager(self, prefix="test_", suffix=".log"):
        """一時ファイル管理インスタンスの作成
        
        Args:
            prefix: ファイル名のプレフィックス
            suffix: ファイル名のサフィックス
            
        Returns:
            作成されたTestFileManagerインスタンス
        """
        file_manager = TestFileManager(prefix, suffix)
        self.file_managers.append(file_manager)
        return file_manager
    
    def cleanup(self):
        """環境の復元"""
        # 作成した一時ファイル管理インスタンスのクリーンアップ
        for file_manager in self.file_managers:
            file_manager.cleanup()
        
        # 環境変数の復元
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def __enter__(self):
        """コンテキストマネージャのエントリーポイント"""
        self.setup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャの終了処理"""
        self.cleanup()


class LogTestEnvironment(TestEnvironment):
    """ロギングテスト用環境クラス
    
    ロギングのテストに特化した環境設定を提供します。
    """
    
    def __init__(self, env_name="test"):
        """初期化
        
        Args:
            env_name: 環境名（test/development/production）
        """
        super().__init__()
        self.env_name = env_name
        self.log_file_manager = None
        self.log_file_path = None
    
    def setup(self):
        """ロギング環境のセットアップ"""
        super().setup()
        
        # 一時ログファイルの作成
        self.log_file_manager = self.create_temp_file_manager(prefix="rmf_log_", suffix=".log")
        logs_dir = self.log_file_manager.create_subdirectory("logs")
        self.log_file_path = logs_dir / "test.log"
        
        # 環境変数の設定
        self.set_env_vars({
            'RMF_ENV': self.env_name,
            'RMF_LOG_LEVEL': 'DEBUG',
            'RMF_LOG_FILE': str(self.log_file_path),
            'RMF_LOG_FORMAT': 'json'
        })
    
    def get_log_entries(self):
        """ログエントリの取得
        
        Returns:
            ログエントリのリスト（JSONオブジェクト）
        """
        if not self.log_file_path.exists():
            return []
        
        try:
            # ロギングバッファを確実にフラッシュ
            for logger_name in ['rmf', 'root']:
                logger = logging.getLogger(logger_name)
                for handler in logger.handlers:
                    handler.flush()
            
            # ファイルオープン前に少し待機（特にWindows環境で重要）
            if PlatformUtils.is_windows():
                time.sleep(0.1)
            
            # ログファイルの内容を読み込み
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                return []
            
            # ログエントリをパース
            return [json.loads(line) for line in content.splitlines() if line.strip()]
        
        except Exception as e:
            print(f"ログエントリの取得中にエラーが発生しました: {e}")
            return []
    
    def find_log_entries(self, level=None, message_contains=None):
        """条件に一致するログエントリを検索
        
        Args:
            level: ログレベル（INFO/DEBUG/ERROR等）
            message_contains: メッセージに含まれる文字列
        
        Returns:
            条件に一致するログエントリのリスト
        """
        entries = self.get_log_entries()
        result = []
        
        for entry in entries:
            match = True
            
            if level and entry.get('level') != level:
                match = False
            
            if message_contains and message_contains not in entry.get('message', ''):
                match = False
            
            if match:
                result.append(entry)
        
        return result


@pytest.fixture
def test_env():
    """テスト環境のフィクスチャ"""
    env = TestEnvironment()
    with env:
        yield env


@pytest.fixture
def log_test_env():
    """ロギングテスト用環境のフィクスチャ"""
    env = LogTestEnvironment()
    with env:
        yield env


@pytest.fixture
def temp_log_file():
    """一時ログファイルのフィクスチャ"""
    file_manager = TestFileManager(prefix="log_", suffix=".log")
    log_dir = file_manager.create_subdirectory("logs")
    log_file = log_dir / "test.log"
    
    # 環境変数の設定
    original_env = os.environ.copy()
    os.environ['RMF_LOG_FILE'] = str(log_file)
    os.environ['RMF_LOG_LEVEL'] = 'DEBUG'
    os.environ['RMF_LOG_FORMAT'] = 'json'
    
    yield log_file
    
    # 環境変数の復元
    os.environ.clear()
    os.environ.update(original_env)
    
    # リソースの解放
    file_manager.cleanup() 