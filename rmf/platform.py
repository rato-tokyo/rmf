"""プラットフォーム依存の処理を抽象化するモジュール

Windows/Linux/Mac環境での動作の違いを吸収します。
"""

import os
import sys
import time
import shutil
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class PlatformUtils:
    """プラットフォーム固有の処理を抽象化するユーティリティクラス"""
    
    @staticmethod
    def is_windows():
        """Windows環境かどうかを判定"""
        return os.name == 'nt'
    
    @staticmethod
    def get_safe_path(path):
        """OS対応パス取得
        
        Args:
            path: 変換対象のパス
            
        Returns:
            str: OS依存の形式に変換されたパス
        """
        path_obj = Path(path)
        return str(path_obj.resolve())
    
    @staticmethod
    def ensure_directory(path):
        """ディレクトリが確実に存在することを保証
        
        Args:
            path: 作成するディレクトリのパス
            
        Returns:
            Path: 作成されたディレクトリのパスオブジェクト
        """
        dir_path = Path(path)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def safe_rmtree(path, max_retries=3, retry_delay=0.2):
        """安全なディレクトリ削除（Windows対応）
        
        Args:
            path: 削除するディレクトリのパス
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）
            
        Returns:
            bool: 削除成功時True
        """
        path = Path(path)
        if not path.exists():
            return True
            
        for i in range(max_retries):
            try:
                if i > 0:
                    logger.debug(f"Retrying rmtree for {path} (attempt {i+1}/{max_retries})")
                
                # Windowsの場合、読み取り専用属性を解除
                if PlatformUtils.is_windows():
                    try:
                        for item in path.rglob('*'):
                            if item.is_file():
                                item.chmod(0o777)
                    except Exception as e:
                        logger.debug(f"Failed to remove read-only attribute: {e}")
                
                shutil.rmtree(path, ignore_errors=True)
                if not path.exists():
                    return True
            except Exception as e:
                logger.debug(f"Failed to remove directory {path}: {e}")
                if i < max_retries - 1:  # 最後の試行以外はリトライ
                    time.sleep(retry_delay)
        
        return not path.exists()
    
    @staticmethod
    def safe_file_write(path, content, encoding='utf-8'):
        """安全なファイル書き込み
        
        Args:
            path: 書き込み先ファイルパス
            content: 書き込む内容
            encoding: 文字エンコーディング
        """
        # 親ディレクトリの作成
        path = Path(path)
        PlatformUtils.ensure_directory(path.parent)
        
        # Windows環境での書き込み前の属性変更
        if PlatformUtils.is_windows() and path.exists():
            try:
                path.chmod(0o777)
            except Exception as e:
                logger.debug(f"Failed to change file attributes: {e}")
        
        # 書き込み処理
        with open(path, 'w', encoding=encoding, newline='\n') as f:
            f.write(content)
            f.flush()
            try:
                os.fsync(f.fileno())  # 確実にディスクに書き込む
            except Exception as e:
                logger.debug(f"Failed to fsync file {path}: {e}")
    
    @staticmethod
    def safe_file_read(path, encoding='utf-8'):
        """安全なファイル読み込み
        
        Args:
            path: 読み込むファイルパス
            encoding: 文字エンコーディング
            
        Returns:
            str or None: ファイルの内容、エラー時はNone
        """
        path = Path(path)
        
        if not path.exists():
            return None
            
        try:
            # Windows環境での読み込み前の属性変更
            if PlatformUtils.is_windows():
                try:
                    path.chmod(0o777)
                except Exception as e:
                    logger.debug(f"Failed to change file attributes: {e}")
            
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            logger.debug(f"Failed to read file {path}: {e}")
            return None 