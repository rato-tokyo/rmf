"""設定管理モジュール

dynaconfを使用して設定を管理します。
環境変数RMF_ENVで環境を切り替えます：
- production: 本番環境（デフォルト）
- test: テスト環境
- development: 開発環境
"""

from dynaconf import Dynaconf
from typing import Dict, Any, List

settings = Dynaconf(
    envvar_prefix="RMF",
    settings_files=["settings.toml"],
    environments=True,
    load_dotenv=True,
)

class Config:
    """設定管理クラス"""
    
    def __init__(self):
        self._settings = settings
    
    @property
    def remote_mcps(self) -> List[Dict[str, Any]]:
        """リモートMCPの設定を取得"""
        return self._settings.remote_mcps
    
    @property
    def logging(self) -> Dict[str, Any]:
        """ロギングの設定を取得"""
        return self._settings.logging
    
    @property
    def server(self) -> Dict[str, Any]:
        """サーバーの設定を取得"""
        return self._settings.server
    
    def get_config(self) -> Dict[str, Any]:
        """全ての設定を取得"""
        return {
            "remote_mcps": self.remote_mcps,
            "logging": self.logging,
            "server": self.server,
        }

# シングルトンインスタンス
config = Config() 