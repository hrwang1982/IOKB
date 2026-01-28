"""
大模型告警分析服务
使用LLM进行问题定位和分析
配置从 config/alert.yaml 读取
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.llm.gateway import llm_service, Message, LLMResponse
from app.core.alert.analyzer import AlertContext
from app.core.alert.config import alert_config


@dataclass
class AnalysisResult:
    """分析结果"""
    summary: str
    root_causes: List[str]
    impact_scope: str
    solutions: List[str]
    prevention: List[str]
    raw_response: str
    confidence: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0


class LLMAlertAnalyzer:
    """大模型告警分析器（使用配置文件）"""
    
    def __init__(self):
        # 从配置文件加载参数
        config = alert_config.llm_analyzer
        self.max_related_alerts = config.max_related_alerts
        self.max_logs = config.max_logs
        self.temperature = config.temperature
        
        # 加载Prompt模板
        self.system_prompt = alert_config.prompts.system_prompt
        self.user_prompt_template = alert_config.prompts.user_prompt
    
    async def analyze(
        self,
        context: AlertContext,
    ) -> AnalysisResult:
        """分析告警"""
        # 构建提示词
        prompt = self._build_prompt(context)
        
        # 调用LLM
        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=prompt),
        ]
        
        try:
            logger.info(f"=== 开始调用大模型进行告警智能分析: alert_id={context.alert.get('alert_id')} ===")
            response = await llm_service.chat(
                messages,
                temperature=self.temperature,
            )
            logger.info(f"=== 告警智能分析调用结束: alert_id={context.alert.get('alert_id')} ===")
            
            # 解析响应
            result = self._parse_response(response)
            
            logger.info(f"告警分析完成: {context.alert.get('alert_id')}")
            return result
            
        except Exception as e:
            logger.error(f"告警分析失败: {e}")
            return AnalysisResult(
                summary="分析失败",
                root_causes=["无法完成分析"],
                impact_scope="未知",
                solutions=["请人工排查"],
                prevention=[],
                raw_response=str(e),
                confidence=0.0,
            )
    
    def _build_prompt(self, context: AlertContext) -> str:
        """构建提示词"""
        alert = context.alert
        
        # CI信息
        ci_info = "无关联配置项"
        if context.ci:
            ci = context.ci
            ci_info = f"""
- 名称: {ci.get('name')}
- 类型: {ci.get('type_name')} ({ci.get('type')})
- 状态: {ci.get('status')}
- 属性: {ci.get('attributes', {})}
"""
        
        # 相关告警
        related_alerts = "无相关告警"
        if context.related_alerts:
            alerts_list = context.related_alerts[:self.max_related_alerts]
            related_lines = []
            for ra in alerts_list:
                related_lines.append(
                    f"- [{ra.get('level')}] {ra.get('title')} ({ra.get('alert_time')})"
                )
            related_alerts = "\n".join(related_lines)
        
        # 性能数据
        performance_data = "无性能数据"
        if context.performance_data:
            # 按指标分组汇总
            metrics = {}
            for p in context.performance_data:
                metric = p.get("metric", "unknown")
                value = p.get("value", 0)
                if metric not in metrics:
                    metrics[metric] = []
                metrics[metric].append(value)
            
            perf_lines = []
            for metric, values in metrics.items():
                if values:
                    avg = sum(values) / len(values)
                    max_val = max(values)
                    perf_lines.append(f"- {metric}: 平均={avg:.2f}, 最大={max_val:.2f}")
            
            if perf_lines:
                performance_data = "\n".join(perf_lines)
        
        # 相关日志
        related_logs = "无相关错误日志"
        if context.related_logs:
            logs_list = context.related_logs[:self.max_logs]
            log_lines = []
            for log in logs_list:
                msg = log.get("message", "")[:200]  # 截断长消息
                log_lines.append(f"- [{log.get('log_level')}] {msg}")
            related_logs = "\n".join(log_lines)
        
        # 拓扑关系
        topology_info = "无关联拓扑信息"
        if context.topology and (context.topology.get("upstream") or context.topology.get("downstream")):
            topo_lines = []
            
            # 上游（影响分析）
            upstream = context.topology.get("upstream", [])
            if upstream:
                topo_lines.append("上游依赖（可能受影响的业务/服务）:")
                for item in upstream:
                    topo_lines.append(f"  - [{item.get('type')}] {item.get('name')} (关系: {item.get('rel_type')})")
            
            # 下游（根因分析）
            downstream = context.topology.get("downstream", [])
            if downstream:
                topo_lines.append("下游依赖（可能的故障根因）:")
                for item in downstream:
                    topo_lines.append(f"  - [{item.get('type')}] {item.get('name')} (关系: {item.get('rel_type')})")
            
            topology_info = "\n".join(topo_lines)
        
        return self.user_prompt_template.format(
            alert_id=alert.get("alert_id", "N/A"),
            level=alert.get("level", "N/A"),
            title=alert.get("title", "N/A"),
            content=alert.get("content", "N/A"),
            source=alert.get("source", "N/A"),
            alert_time=alert.get("alert_time", "N/A"),
            ci_identifier=alert.get("ci_identifier", "N/A"),
            ci_info=ci_info,
            related_count=len(context.related_alerts),
            related_alerts=related_alerts,
            performance_data=performance_data,
            log_count=len(context.related_logs),
            related_logs=related_logs,
            topology_info=topology_info,  # Add topology info to format
        )
    
    def _parse_response(self, response: LLMResponse) -> AnalysisResult:
        """解析LLM响应"""
        content = response.content
        
        # 简单解析（按标题分段）
        sections = {
            "summary": "",
            "root_causes": [],
            "impact_scope": "",
            "solutions": [],
            "prevention": [],
        }
        
        current_section = None
        lines = content.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 识别章节标题
            if "问题概述" in line or "概述" in line:
                current_section = "summary"
                continue
            elif "根因分析" in line or "根因" in line or "原因" in line:
                current_section = "root_causes"
                continue
            elif "影响范围" in line or "影响" in line:
                current_section = "impact_scope"
                continue
            elif "解决建议" in line or "解决方案" in line or "解决" in line:
                current_section = "solutions"
                continue
            elif "预防措施" in line or "预防" in line:
                current_section = "prevention"
                continue
            
            # 添加内容到当前章节
            if current_section:
                # 去除列表标记
                clean_line = line.lstrip("- •1234567890.)")
                if clean_line:
                    if current_section in ["root_causes", "solutions", "prevention"]:
                        sections[current_section].append(clean_line)
                    else:
                        sections[current_section] += " " + clean_line
        
        return AnalysisResult(
            summary=sections["summary"].strip() or "分析完成",
            root_causes=sections["root_causes"] or ["需要进一步排查"],
            impact_scope=sections["impact_scope"].strip() or "待评估",
            solutions=sections["solutions"] or ["请人工排查"],
            prevention=sections["prevention"],
            raw_response=content,
            confidence=0.8,  # 简化处理，后续可以根据响应质量评估
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )


# 创建全局分析器实例
llm_alert_analyzer = LLMAlertAnalyzer()
