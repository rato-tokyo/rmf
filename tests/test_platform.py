"""プラットフォームユーティリティのテスト"""

import os
import sys
import time
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from rmf.platform import PlatformUtils


@pytest.fixture
def temp_dir(tmp_path):
    """一時ディレクトリを提供するフィクスチャ"""
    return tmp_path


def test_is_windows():
    """Windows環境判定のテスト"""
    with patch('os.name', 'nt'):
        assert PlatformUtils.is_windows() is True
    
    with patch('os.name', 'posix'):
        assert PlatformUtils.is_windows() is False


def test_get_safe_path():
    """OS対応パス取得のテスト"""
    # Windowsパスのテスト
    with patch('pathlib.Path.resolve', return_value=Path('C:/test/path')):
        path = PlatformUtils.get_safe_path('test/path')
        assert isinstance(path, str)
        # プラットフォームに応じたパス区切り文字をチェック
        if os.name == 'nt':
            assert '\\' in path
        else:
            assert '/' in path
    
    # Unixパスのテスト
    with patch('pathlib.Path.resolve', return_value=Path('/test/path')):
        path = PlatformUtils.get_safe_path('test/path')
        assert isinstance(path, str)
        # プラットフォームに応じたパス区切り文字をチェック
        if os.name == 'nt':
            assert '\\' in path
        else:
            assert '/' in path


def test_ensure_directory(temp_dir):
    """ディレクトリ作成保証のテスト"""
    # 単一ディレクトリの作成
    test_dir = temp_dir / 'test_dir'
    result = PlatformUtils.ensure_directory(test_dir)
    assert result.exists()
    assert result.is_dir()
    
    # 既存ディレクトリの確認
    result = PlatformUtils.ensure_directory(test_dir)
    assert result.exists()
    assert result.is_dir()
    
    # ネストしたディレクトリの作成
    nested_dir = temp_dir / 'parent' / 'child' / 'grandchild'
    result = PlatformUtils.ensure_directory(nested_dir)
    assert result.exists()
    assert result.is_dir()
    assert (temp_dir / 'parent' / 'child').exists()


def test_safe_rmtree(temp_dir):
    """安全なディレクトリ削除のテスト"""
    # 通常の削除
    test_dir = temp_dir / 'test_dir'
    test_dir.mkdir()
    (test_dir / 'test_file.txt').write_text('test')
    
    assert PlatformUtils.safe_rmtree(test_dir) is True
    assert not test_dir.exists()
    
    # 存在しないディレクトリの削除
    assert PlatformUtils.safe_rmtree(temp_dir / 'not_exists') is True
    
    # 削除失敗のシミュレーション
    def mock_rmtree(*args, **kwargs):
        raise PermissionError()
    
    with patch('shutil.rmtree', side_effect=mock_rmtree):
        test_dir.mkdir()
        assert PlatformUtils.safe_rmtree(test_dir, max_retries=2, retry_delay=0.1) is False


def test_safe_file_write(temp_dir):
    """安全なファイル書き込みのテスト"""
    # 通常の書き込み
    test_file = temp_dir / 'test.txt'
    content = 'テストコンテンツ'
    PlatformUtils.safe_file_write(test_file, content)
    
    assert test_file.exists()
    assert test_file.read_text(encoding='utf-8') == content
    
    # ディレクトリ自動作成の確認
    nested_file = temp_dir / 'nested' / 'dir' / 'test.txt'
    PlatformUtils.safe_file_write(nested_file, content)
    
    assert nested_file.exists()
    assert nested_file.read_text(encoding='utf-8') == content
    
    # fsyncエラーのテスト
    def mock_fsync(*args):
        raise OSError()
    
    with patch('os.fsync', side_effect=mock_fsync):
        PlatformUtils.safe_file_write(test_file, 'new content')
        assert test_file.read_text(encoding='utf-8') == 'new content'


def test_safe_file_read(temp_dir):
    """安全なファイル読み込みのテスト"""
    # 通常の読み込み
    test_file = temp_dir / 'test.txt'
    content = 'テストコンテンツ'
    test_file.write_text(content, encoding='utf-8')
    
    assert PlatformUtils.safe_file_read(test_file) == content
    
    # 存在しないファイルの読み込み
    assert PlatformUtils.safe_file_read(temp_dir / 'not_exists.txt') is None
    
    # 読み込みエラーのテスト
    def mock_open(*args, **kwargs):
        raise PermissionError()
    
    with patch('builtins.open', side_effect=mock_open):
        assert PlatformUtils.safe_file_read(test_file) is None


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows specific test')
def test_windows_specific_behaviors(temp_dir):
    """Windows固有の動作テスト"""
    import msvcrt
    import win32file
    import win32con
    
    # ロックされたファイルの削除テスト
    test_dir = temp_dir / 'locked_dir'
    test_dir.mkdir()
    test_file = test_dir / 'locked.txt'
    
    # ファイルを作成してロックを取得
    handle = win32file.CreateFile(
        str(test_file),
        win32con.GENERIC_READ | win32con.GENERIC_WRITE,
        0,  # 共有モードなし
        None,
        win32con.CREATE_NEW,
        win32con.FILE_ATTRIBUTE_NORMAL,
        None
    )
    
    try:
        # ファイルがロックされた状態でディレクトリ削除を試みる
        result = PlatformUtils.safe_rmtree(test_dir, max_retries=3, retry_delay=0.1)
        assert result is False  # ロックされているので削除は失敗するはず
    finally:
        # クリーンアップ
        handle.Close()
        # ロック解除後は削除できることを確認
        assert PlatformUtils.safe_rmtree(test_dir) is True 