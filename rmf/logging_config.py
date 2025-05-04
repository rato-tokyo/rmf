"""RMF用のロギング設定"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional, Dict, Any

class RMFLogger:
    """RMF用のロガークラス"""
    
    def __init__(self, name: str = "rmf", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # フォーマッタの作成
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # コンソールハンドラの設定
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # ファイルハンドラの設定（指定がある場合）
        if log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, msg: str, **kwargs):
        """デバッグログを出力"""
        self._log(logging.DEBUG, msg, **kwargs)
    
    def info(self, msg: str, **kwargs):
        """情報ログを出力"""
        self._log(logging.INFO, msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        """警告ログを出力"""
        self._log(logging.WARNING, msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        """エラーログを出力"""
        self._log(logging.ERROR, msg, **kwargs)
    
    def critical(self, msg: str, **kwargs):
        """重大エラーログを出力"""
        self._log(logging.CRITICAL, msg, **kwargs)
    
    def _log(self, level: int, msg: str, **kwargs):
        """ログ出力の共通処理"""
        # extraには予約語を避けた情報だけを格納
        extra = {}
        
        # 基本コンテキスト情報の作成
        context = {
            'timestamp': datetime.now().isoformat(),
            'trace_id': kwargs.get('trace_id', 'N/A'),
            'function': kwargs.get('function', 'N/A')
        }
        
        # 追加情報があれば追加
        details = kwargs.get('details', {})
        if isinstance(details, dict):
            context.update(details)
        
        # 直接extraに渡された情報を追加
        user_extra = kwargs.get('extra', {})
        if isinstance(user_extra, dict):
            # 予約語を避ける
            for key, value in user_extra.items():
                if key not in ['message', 'asctime']:
                    context[key] = value
        
        # extraにはコンテキスト情報を追加（テスト用）
        extra['rmf_context'] = context
        
        # メッセージの整形
        formatted_msg = f"{msg} | Context: {context}"
        
        # ログ出力
        self.logger.log(level, formatted_msg, extra=extra)

def setup_logger(name: str = "rmf", log_file: Optional[str] = None) -> RMFLogger:
    """ロガーのセットアップ用ヘルパー関数"""
    return RMFLogger(name, log_file) 