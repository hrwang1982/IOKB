"""
告警模块配置管理
从YAML配置文件加载配置
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger


@dataclass
class EnricherConfig:
    """告警丰富器配置"""
    time_window_minutes: int = 30
    max_related_alerts: int = 10
    max_logs: int = 50
    performance_metrics: List[str] = field(default_factory=lambda: [
        "cpu_usage", "memory_usage", "disk_usage", "network_io"
    ])


@dataclass
class CorrelatorConfig:
    """告警关联器配置"""
    correlation_window_minutes: int = 10
    min_correlation_score: float = 0.5
    max_correlated_alerts: int = 100


@dataclass
class LLMAnalyzerConfig:
    """LLM分析器配置"""
    max_related_alerts: int = 5
    max_logs: int = 20
    temperature: float = 0.3
    max_tokens: int = 2048


@dataclass
class RecommenderConfig:
    """方案推荐器配置"""
    max_recommendations: int = 5
    min_relevance_score: float = 0.5
    use_rag_answer: bool = True


@dataclass
class PromptsConfig:
    """Prompt模板配置"""
    system_prompt: str = ""
    user_prompt: str = ""
    quick_analysis_prompt: str = ""


@dataclass
class AlertLevelConfig:
    """告警级别配置"""
    priority: int
    default_categories: List[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    """告警模块完整配置"""
    enricher: EnricherConfig = field(default_factory=EnricherConfig)
    correlator: CorrelatorConfig = field(default_factory=CorrelatorConfig)
    llm_analyzer: LLMAnalyzerConfig = field(default_factory=LLMAnalyzerConfig)
    recommender: RecommenderConfig = field(default_factory=RecommenderConfig)
    prompts: PromptsConfig = field(default_factory=PromptsConfig)
    keyword_mappings: Dict[str, List[str]] = field(default_factory=dict)
    alert_levels: Dict[str, AlertLevelConfig] = field(default_factory=dict)


class AlertConfigLoader:
    """告警配置加载器"""
    
    DEFAULT_CONFIG_PATHS = [
        "config/alert.yaml",
        "config/alert.yml",
        "../config/alert.yaml",
        "/etc/skb/alert.yaml",
    ]
    
    # 默认Prompt模板
    DEFAULT_SYSTEM_PROMPT = """你是一位资深的IT运维专家，专门负责分析系统告警、定位问题根因并提供解决建议。

你的职责是：
1. 分析告警信息，理解问题本质
2. 结合关联的性能数据、日志信息进行综合判断
3. 找出可能的问题根因
4. 提供切实可行的解决方案

请始终保持专业、准确、简洁。"""

    DEFAULT_USER_PROMPT = """请分析以下告警及其上下文信息：

## 当前告警
- **告警ID**: {alert_id}
- **告警级别**: {level}
- **告警标题**: {title}
- **告警内容**: {content}
- **告警来源**: {source}
- **告警时间**: {alert_time}
- **配置项**: {ci_identifier}

## 关联的配置项信息
{ci_info}

## 近期相关告警（{related_count}条）
{related_alerts}

## 相关性能数据
{performance_data}

## 相关错误日志（{log_count}条）
{related_logs}

---

请提供以下分析结果：
1. **问题概述**: 简要描述当前问题
2. **根因分析**: 可能的问题根因（优先级排序）
3. **影响范围**: 评估此问题可能的影响范围
4. **解决建议**: 具体的解决步骤
5. **预防措施**: 如何避免此类问题再次发生"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self._config: Optional[AlertConfig] = None
        self._raw_config: Dict[str, Any] = {}
    
    def _find_config_file(self) -> Optional[str]:
        """查找配置文件"""
        if self.config_path and os.path.exists(self.config_path):
            return self.config_path
        
        # 从项目根目录开始查找
        base_dir = Path(__file__).parent.parent.parent.parent
        
        for path in self.DEFAULT_CONFIG_PATHS:
            full_path = base_dir / path
            if full_path.exists():
                return str(full_path)
        
        return None
    
    def _load_yaml(self) -> Dict[str, Any]:
        """加载YAML配置"""
        config_file = self._find_config_file()
        
        if not config_file:
            logger.warning("未找到告警配置文件，使用默认配置")
            return {}
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                logger.info(f"加载告警配置文件: {config_file}")
                return data or {}
        except Exception as e:
            logger.error(f"加载告警配置文件失败: {e}")
            return {}
    
    def load(self) -> AlertConfig:
        """加载配置"""
        if self._config is not None:
            return self._config
        
        self._raw_config = self._load_yaml()
        
        # 解析enricher配置
        enricher_data = self._raw_config.get("enricher", {})
        enricher = EnricherConfig(
            time_window_minutes=enricher_data.get("time_window_minutes", 30),
            max_related_alerts=enricher_data.get("max_related_alerts", 10),
            max_logs=enricher_data.get("max_logs", 50),
            performance_metrics=enricher_data.get("performance_metrics", [
                "cpu_usage", "memory_usage", "disk_usage", "network_io"
            ]),
        )
        
        # 解析correlator配置
        correlator_data = self._raw_config.get("correlator", {})
        correlator = CorrelatorConfig(
            correlation_window_minutes=correlator_data.get("correlation_window_minutes", 10),
            min_correlation_score=correlator_data.get("min_correlation_score", 0.5),
            max_correlated_alerts=correlator_data.get("max_correlated_alerts", 100),
        )
        
        # 解析llm_analyzer配置
        llm_data = self._raw_config.get("llm_analyzer", {})
        llm_analyzer = LLMAnalyzerConfig(
            max_related_alerts=llm_data.get("max_related_alerts", 5),
            max_logs=llm_data.get("max_logs", 20),
            temperature=llm_data.get("temperature", 0.3),
            max_tokens=llm_data.get("max_tokens", 2048),
        )
        
        # 解析recommender配置
        recommender_data = self._raw_config.get("recommender", {})
        recommender = RecommenderConfig(
            max_recommendations=recommender_data.get("max_recommendations", 5),
            min_relevance_score=recommender_data.get("min_relevance_score", 0.5),
            use_rag_answer=recommender_data.get("use_rag_answer", True),
        )
        
        # 解析prompts配置
        prompts_data = self._raw_config.get("prompts", {})
        prompts = PromptsConfig(
            system_prompt=prompts_data.get("system_prompt", self.DEFAULT_SYSTEM_PROMPT),
            user_prompt=prompts_data.get("user_prompt", self.DEFAULT_USER_PROMPT),
            quick_analysis_prompt=prompts_data.get("quick_analysis_prompt", ""),
        )
        
        # 解析规则匹配配置
        rule_matcher_data = self._raw_config.get("rule_matcher", {})
        keyword_mappings = rule_matcher_data.get("keyword_mappings", {})
        
        # 解析告警级别配置
        alert_levels = {}
        levels_data = self._raw_config.get("alert_levels", {})
        for level_name, level_data in levels_data.items():
            alert_levels[level_name] = AlertLevelConfig(
                priority=level_data.get("priority", 3),
                default_categories=level_data.get("default_categories", []),
            )
        
        self._config = AlertConfig(
            enricher=enricher,
            correlator=correlator,
            llm_analyzer=llm_analyzer,
            recommender=recommender,
            prompts=prompts,
            keyword_mappings=keyword_mappings,
            alert_levels=alert_levels,
        )
        
        return self._config
    
    def reload(self) -> AlertConfig:
        """重新加载配置"""
        self._config = None
        self._raw_config = {}
        return self.load()
    
    def get_raw_config(self) -> Dict[str, Any]:
        """获取原始配置"""
        if not self._raw_config:
            self._raw_config = self._load_yaml()
        return self._raw_config


# 创建全局配置加载器和配置对象
alert_config_loader = AlertConfigLoader()
alert_config = alert_config_loader.load()


def get_alert_config() -> AlertConfig:
    """获取告警配置"""
    return alert_config


def reload_alert_config() -> AlertConfig:
    """重新加载告警配置"""
    global alert_config
    alert_config = alert_config_loader.reload()
    return alert_config
