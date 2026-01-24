"""
应用配置模块
从环境变量加载配置
"""

import json
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # 基础配置
    app_name: str = "SKB"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # MySQL 数据库
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "skb"
    mysql_password: str = ""
    mysql_database: str = "skb"
    
    @property
    def mysql_url(self) -> str:
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    @property
    def mysql_async_url(self) -> str:
        return f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    # Elasticsearch
    es_host: str = "localhost"
    es_port: int = 9200
    es_user: str = "elastic"
    es_password: str = ""
    es_index_prefix: str = "skb"
    
    @property
    def es_url(self) -> str:
        if self.es_user and self.es_password:
            return f"http://{self.es_user}:{self.es_password}@{self.es_host}:{self.es_port}"
        return f"http://{self.es_host}:{self.es_port}"
    
    # InfluxDB
    influxdb_url: str = "http://localhost:8086"
    influxdb_token: str = ""
    influxdb_org: str = "skb"
    influxdb_bucket: str = "metrics"
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_alert_topic: str = "skb-alerts"
    kafka_performance_topic: str = "skb-performance"
    kafka_log_topic: str = "skb-logs"
    kafka_consumer_group: str = "skb-consumer"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # JWT 认证
    jwt_secret_key: str = "your_jwt_secret_key_here"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # LLM 配置
    llm_provider: str = "aliyun"  # aliyun, openai, anthropic, baidu, local, custom
    llm_deploy_mode: str = "api"  # api: 调用API, local: 本地部署
    llm_model_name: str = "qwen-turbo"
    llm_api_key: str = ""
    llm_api_base: str = "https://dashscope.aliyuncs.com/api/v1"
    llm_local_url: str = ""  # 本地部署URL，如 http://localhost:8080/v1
    llm_max_tokens: int = 4096
    llm_max_input_tokens: int = 8192
    llm_max_output_tokens: int = 4096
    llm_temperature: float = 0.7
    
    # Embedding 配置
    embedding_provider: str = "aliyun"  # aliyun, openai, local, custom
    embedding_deploy_mode: str = "api"  # api: 调用API, local: 本地部署
    embedding_model_name: str = "text-embedding-v3"
    embedding_api_key: str = ""
    embedding_api_base: str = ""
    embedding_local_url: str = ""  # 本地部署URL，如 http://localhost:8081/embed
    embedding_dimension: int = 1024
    
    # Rerank 配置
    rerank_provider: str = "aliyun"  # aliyun, local, custom
    rerank_deploy_mode: str = "api"  # api: 调用API, local: 本地部署
    rerank_model_name: str = "gte-rerank"
    rerank_api_key: str = ""
    rerank_api_base: str = ""
    rerank_local_url: str = ""  # 本地部署URL，如 http://localhost:8082/rerank
    
    # OCR 配置
    ocr_provider: str = "paddleocr"  # paddleocr, paddleocr_vl, aliyun, baidu, local, custom
    ocr_deploy_mode: str = "local"  # api: 调用API, local: 本地部署
    ocr_model_name: str = ""  # 模型名称，如 qwen-vl-ocr
    ocr_model_path: str = ""  # 本地模型路径
    ocr_api_key: str = ""
    ocr_api_base: str = ""
    ocr_local_url: str = ""  # 本地部署URL，如 http://localhost:8083/ocr
    
    # ASR 语音识别配置
    asr_provider: str = "aliyun"  # aliyun, local, custom
    asr_deploy_mode: str = "api"  # api: 调用API, local: 本地部署
    asr_model_name: str = "paraformer-v2"  # aliyun: paraformer-v2, openai: whisper-1, local: fun-asr-mtl
    asr_api_key: str = ""
    asr_api_base: str = ""
    asr_local_url: str = ""  # 本地部署URL

    # 多模态VL模型配置（图片理解/视频分析）
    vl_provider: str = "aliyun"  # aliyun, openai, local, custom
    vl_deploy_mode: str = "api"  # api: 调用API, local: 本地部署
    vl_model_name: str = "qwen-vl-max"  # 阿里云: qwen-vl-max/qwen-vl-plus/qwen3-vl-flash
    vl_api_key: str = ""  # 留空则使用llm_api_key
    vl_api_base: str = ""  # 留空则使用对应provider默认值
    vl_local_url: str = ""  # 本地部署URL
    
    # Socket 服务
    socket_host: str = "0.0.0.0"
    socket_port: int = 9000
    
    # 文件存储
    storage_type: str = "local"
    storage_path: str = "./storage"
    
    # LDAP (可选)
    ldap_enabled: bool = False
    ldap_server: str = ""
    ldap_base_dn: str = ""
    ldap_user_search_base: str = ""
    ldap_user_filter: str = "(uid={username})"
    ldap_bind_dn: str = ""
    ldap_bind_password: str = ""
    ldap_user_dn: str = ""
    ldap_password: str = ""
    
    # SSO (可选)
    sso_enabled: bool = False
    sso_provider: str = "oauth2"
    sso_url: str = ""
    sso_client_id: str = ""
    sso_client_secret: str = ""
    sso_authorize_url: str = ""
    sso_token_url: str = ""
    sso_userinfo_url: str = ""
    
    # CORS
    cors_origins: str = '["http://localhost:3000","http://localhost:8000"]'
    
    @property
    def cors_origins_list(self) -> List[str]:
        try:
            return json.loads(self.cors_origins)
        except json.JSONDecodeError:
            return ["*"]


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()
