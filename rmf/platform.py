"""プラットフォーム依存の処理を抽象化するモジュール

Windows/Linux/Mac環境での動作の違いを吸収します。
"""

import os
import sys
import time
import shutil
from pathlib import Path


class PlatformUtils:
    """プラットフォーム固有の処理を抽象化するユーティリティクラス"""
    
    @staticmethod
    def is_windows():
        """Windows環境かどうかを判定"""
        return os.name == 'nt'
    
    @staticmethod
    def get_safe_path(path):
        """OS対応パス取得"""
        path_obj = Path(path)
        return str(path_obj.resolve())
    
    @staticmethod
    def ensure_directory(path):
        """ディレクトリが確実に存在することを保証"""
        dir_path = Path(path)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def safe_rmtree(path, max_retries=3, retry_delay=0.2):
        """安全なディレクトリ削除（Windows対応）"""
        path = Path(path)
        if not path.exists():
            return True
            
        for i in range(max_retries):
            try:
                shutil.rmtree(path, ignore_errors=True)
                if not path.exists():
                    return True
            except Exception:
                pass
            
            # Windowsではファイルハンドルの解放を待つ
            if PlatformUtils.is_windows():
                time.sleep(retry_delay)
        
        return not path.exists()
    
    @staticmethod
    def safe_file_write(path, content, encoding='utf-8'):
        """安全なファイル書き込み"""
        # 親ディレクトリの作成
        path = Path(path)
        PlatformUtils.ensure_directory(path.parent)
        
        # 書き込み処理
        with open(path, 'w', encoding=encoding, newline='\n') as f:
            f.write(content)
            f.flush()
            try:
                os.fsync(f.fileno())  # 確実にディスクに書き込む
            except Exception:
                # fsyncが利用できない場合は無視
                pass
    
    @staticmethod
    def safe_file_read(path, encoding='utf-8'):
        """安全なファイル読み込み"""
        path = Path(path)
        
        if not path.exists():
            return None
            
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception:
            return None 