'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    AlertTriangle,
    ArrowLeft,
    BookOpen,
    Brain,
    CheckCircle,
    ChevronRight,
    Clock,
    Database,
    FileText,
    Lightbulb,
    RefreshCw,
    Server,
    TrendingUp,
    Zap,
    Loader2,
} from 'lucide-react';
import {
    getAlert,
    getAlertAnalysis,
    getAlertSolutions,
    getAlertPerformance,
    getAlertLogs,
    Alert,
    AlertAnalysisResponse,
    SolutionResult
} from '@/lib/api';
import { toast } from 'sonner';

export default function AlertDetailPage({ params }: { params: { id: string } }) {
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);

    // Data States
    const [alert, setAlert] = useState<Alert | null>(null);
    const [analysis, setAnalysis] = useState<AlertAnalysisResponse | null>(null);
    const [solutions, setSolutions] = useState<SolutionResult[]>([]);
    const [performance, setPerformance] = useState<any[]>([]);
    const [logs, setLogs] = useState<any[]>([]);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                // 1. Fetch Basic Alert Info
                const alertData = await getAlert(params.id);
                setAlert(alertData);

                // 2. Parallel fetch for other context
                // We don't block the main UI on these, but for simplicity here we assume they load relatively fast or we could load them separately.
                // Better UX: Load alert first, then others.

                Promise.all([
                    getAlertAnalysis(params.id).catch(err => null),
                    getAlertSolutions(params.id).catch(err => []),
                    getAlertPerformance(params.id).catch(err => ({ metrics: [] })),
                    getAlertLogs(params.id).catch(err => ({ logs: [] }))
                ]).then(([analysisData, solutionsData, perfData, logsData]) => {
                    if (analysisData) setAnalysis(analysisData as AlertAnalysisResponse);
                    if (solutionsData) setSolutions(solutionsData as SolutionResult[]);
                    if (perfData) setPerformance((perfData as any).metrics || []);
                    if (logsData) setLogs((logsData as any).logs || []);
                });

            } catch (error) {
                console.error('Error fetching alert details:', error);
                toast.error('获取告警详情失败');
            } finally {
                setLoading(false);
            }
        };

        if (params.id) {
            fetchData();
        }
    }, [params.id]);

    const handleReanalyze = async () => {
        if (!process.env.NEXT_PUBLIC_ENABLE_REAL_ANALYSIS) {
            // Mock re-analysis effect if not enabled, or just call API
        }

        setAnalyzing(true);
        try {
            const analysisData = await getAlertAnalysis(params.id);
            setAnalysis(analysisData);
            toast.success('智能分析已更新');

            // Also refresh solutions as they might depend on analysis
            const solutionsData = await getAlertSolutions(params.id);
            setSolutions(solutionsData);

        } catch (error) {
            console.error('Analysis failed:', error);
            toast.error('分析失败，请稍后重试');
        } finally {
            setAnalyzing(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!alert) {
        return (
            <div className="flex flex-col items-center justify-center h-screen space-y-4">
                <h1 className="text-2xl font-bold">告警不存在或无权限访问</h1>
                <Link href="/alerts" className="btn-primary">返回列表</Link>
            </div>
        );
    }

    const levelConfig = {
        critical: { label: '紧急', className: 'text-error border-error/30 bg-error/10', icon: AlertTriangle },
        warning: { label: '警告', className: 'text-warning border-warning/30 bg-warning/10', icon: Clock },
        info: { label: '信息', className: 'text-primary border-primary/30 bg-primary/10', icon: CheckCircle },
    };

    const level = levelConfig[alert.level as keyof typeof levelConfig] || levelConfig.info;
    const LevelIcon = level.icon;

    // Helper for formatting date
    const formatDate = (dateString: string) => {
        try { return new Date(dateString).toLocaleString('zh-CN'); } catch { return dateString; }
    };

    return (
        <div className="space-y-6 animate-fade-in pb-12">
            {/* 面包屑 */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Link href="/alerts" className="hover:text-primary flex items-center gap-1">
                    <ArrowLeft className="h-4 w-4" />
                    告警列表
                </Link>
                <ChevronRight className="h-4 w-4" />
                <span className="text-foreground">{alert.alert_id}</span>
            </div>

            {/* 告警标题栏 */}
            <div className="card p-6">
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-lg ${level.className.split(' ')[2]}`}> {/* Use bg color */}
                            <LevelIcon className={`h-6 w-6 ${level.className.split(' ')[0]}`} />
                        </div>
                        <div>
                            <div className="flex items-center gap-3">
                                <h1 className="text-xl font-bold text-foreground">{alert.title}</h1>
                                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${level.className}`}>
                                    {level.label}
                                </span>
                            </div>
                            <p className="text-muted-foreground mt-2">{alert.content}</p>
                            <div className="flex items-center gap-6 mt-4 text-sm text-muted-foreground">
                                <span className="flex items-center gap-1">
                                    <Clock className="h-4 w-4" />
                                    {formatDate(alert.alert_time)}
                                </span>
                                <span className="flex items-center gap-1">
                                    <Server className="h-4 w-4" />
                                    {alert.ci_name || alert.tags?.ci_identifier}
                                </span>
                                <span className="flex items-center gap-1">
                                    <Database className="h-4 w-4" />
                                    {alert.source}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button className="btn-outline">确认告警</button>
                        <button className="btn-primary">解决告警</button>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 左侧：智能分析 */}
                <div className="lg:col-span-2 space-y-6">
                    {/* 智能分析结果 */}
                    <div className="card">
                        <div className="p-4 border-b border-border flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Brain className="h-5 w-5 text-primary" />
                                <h2 className="font-semibold text-foreground">智能分析</h2>
                            </div>
                            <button
                                onClick={handleReanalyze}
                                disabled={analyzing}
                                className="btn-ghost text-sm flex items-center gap-1"
                            >
                                <RefreshCw className={`h-4 w-4 ${analyzing ? 'animate-spin' : ''}`} />
                                {analyzing ? '分析中...' : '重新分析'}
                            </button>
                        </div>

                        {analysis ? (
                            <div className="p-6 space-y-6">
                                {/* 摘要 */}
                                <div>
                                    <h3 className="text-sm font-medium text-muted-foreground mb-2">问题摘要</h3>
                                    <p className="text-foreground">{analysis.analysis.fault_summary}</p>
                                </div>

                                {/* 可能原因 */}
                                <div>
                                    <h3 className="text-sm font-medium text-muted-foreground mb-3">可能原因</h3>
                                    <div className="space-y-2">
                                        {analysis.analysis.possible_causes.map((cause, index) => (
                                            <div key={index} className="flex items-start gap-2">
                                                <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                                                <span className="text-sm text-foreground">{cause}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* 影响范围 */}
                                <div>
                                    <h3 className="text-sm font-medium text-muted-foreground mb-2">影响范围</h3>
                                    <p className="text-foreground">{analysis.analysis.impact_scope}</p>
                                </div>

                                {/* 建议措施 */}
                                <div>
                                    <h3 className="text-sm font-medium text-muted-foreground mb-3">建议措施</h3>
                                    <ol className="space-y-2">
                                        {analysis.analysis.suggested_actions.map((action, index) => (
                                            <li key={index} className="flex items-start gap-2 text-foreground">
                                                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary/10 text-primary text-xs font-medium shrink-0 mt-0.5">
                                                    {index + 1}
                                                </span>
                                                {action}
                                            </li>
                                        ))}
                                    </ol>
                                </div>

                                {/* 风险等级 */}
                                <div className="pt-4 border-t border-border flex items-center justify-between">
                                    <span className="text-sm text-muted-foreground">风险等级</span>
                                    <span className={`text-sm font-medium ${analysis.analysis.risk_level === 'high' ? 'text-error' :
                                            analysis.analysis.risk_level === 'medium' ? 'text-warning' : 'text-primary'
                                        }`}>
                                        {analysis.analysis.risk_level.toUpperCase()}
                                    </span>
                                </div>
                            </div>
                        ) : (
                            <div className="p-8 text-center text-muted-foreground">
                                {analyzing ? '正在分析告警根因...' : '暂无分析结果，请点击重新分析'}
                            </div>
                        )}
                    </div>

                    {/* 推荐方案 */}
                    <div className="card">
                        <div className="p-4 border-b border-border flex items-center gap-2">
                            <Lightbulb className="h-5 w-5 text-accent" />
                            <h2 className="font-semibold text-foreground">推荐处理方案</h2>
                        </div>
                        <div className="divide-y divide-border">
                            {solutions.length > 0 ? solutions.map((solution) => (
                                <div
                                    key={solution.id}
                                    className="p-4 hover:bg-accent/5 transition-colors cursor-pointer"
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <FileText className="h-4 w-4 text-primary" />
                                                <h3 className="font-medium text-foreground">{solution.title}</h3>
                                            </div>
                                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                                {solution.content}
                                            </p>
                                            <span className="inline-block mt-2 text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                                                来源: {solution.source}
                                            </span>
                                        </div>
                                        <div className="ml-4 text-right">
                                            <div className="text-lg font-bold text-primary">
                                                {Math.round(solution.relevance_score * 100)}%
                                            </div>
                                            <div className="text-xs text-muted-foreground">匹配度</div>
                                        </div>
                                    </div>
                                </div>
                            )) : (
                                <div className="p-6 text-center text-muted-foreground text-sm">
                                    暂无推荐方案
                                </div>
                            )}
                        </div>
                    </div>

                    {/* 关联日志 */}
                    <div className="card">
                        <div className="p-4 border-b border-border flex items-center gap-2">
                            <FileText className="h-5 w-5 text-muted-foreground" />
                            <h2 className="font-semibold text-foreground">关联日志</h2>
                        </div>
                        <div className="p-4 font-mono text-sm bg-dark-bg rounded-b-lg overflow-x-auto">
                            {logs.length > 0 ? logs.map((log, index) => (
                                <div key={index} className="flex gap-4 py-1">
                                    <span className="text-muted-foreground shrink-0">{formatDate(log.timestamp).split(' ')[1]}</span>
                                    <span
                                        className={`shrink-0 ${log.log_level === 'error' || log.log_level === 'critical' ? 'text-error' :
                                                log.log_level === 'warning' ? 'text-warning' : 'text-muted-foreground'
                                            }`}
                                    >
                                        [{log.log_level?.toUpperCase()}]
                                    </span>
                                    <span className="text-foreground whitespace-pre-wrap">{log.message}</span>
                                </div>
                            )) : (
                                <div className="text-muted-foreground text-center">无相关日志数据</div>
                            )}
                        </div>
                    </div>
                </div>

                {/* 右侧：配置项信息和性能数据 */}
                <div className="space-y-6">
                    {/* 配置项信息 */}
                    <div className="card">
                        <div className="p-4 border-b border-border flex items-center gap-2">
                            <Server className="h-5 w-5 text-muted-foreground" />
                            <h2 className="font-semibold text-foreground">配置项信息</h2>
                        </div>
                        <div className="p-4 space-y-3">
                            {[
                                { label: '标识符', value: alert.ci_name || alert.tags?.ci_identifier },
                                { label: '类型', value: alert.tags?.ci_type },
                                { label: '来源', value: alert.source },
                            ].map((item) => (
                                item.value && (
                                    <div key={item.label} className="flex justify-between text-sm">
                                        <span className="text-muted-foreground">{item.label}</span>
                                        <span className="text-foreground">{item.value}</span>
                                    </div>
                                )
                            ))}
                            {alert.ci_id && (
                                <Link
                                    href={`/cmdb/${alert.ci_id}`}
                                    className="block pt-3 border-t border-border text-sm text-primary hover:underline"
                                >
                                    查看配置项详情 →
                                </Link>
                            )}
                        </div>
                    </div>

                    {/* 实时性能 */}
                    <div className="card">
                        <div className="p-4 border-b border-border flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-muted-foreground" />
                            <h2 className="font-semibold text-foreground">关联指标 (近1小时)</h2>
                        </div>
                        <div className="p-4 space-y-4">
                            {performance.length > 0 ? performance.slice(0, 5).map((item, i) => (
                                <div key={i}>
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm text-muted-foreground">{item.metric_name}</span>
                                        <span className="text-sm font-medium text-foreground">
                                            {Number(item.value).toFixed(2)} {item.unit}
                                        </span>
                                    </div>
                                    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-primary rounded-full"
                                            style={{
                                                width: `${Math.min(item.value, 100)}%`
                                            }}
                                        />
                                    </div>
                                </div>
                            )) : (
                                <div className="text-sm text-muted-foreground text-center">暂无性能数据</div>
                            )}
                        </div>
                    </div>

                    {/* 快捷操作 */}
                    <div className="card p-4 space-y-2">
                        <button className="btn-outline w-full justify-start gap-2">
                            <BookOpen className="h-4 w-4" />
                            搜索知识库
                        </button>
                        <button className="btn-outline w-full justify-start gap-2">
                            <Zap className="h-4 w-4" />
                            执行自动修复
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
