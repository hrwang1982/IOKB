'use client';

import { useState } from 'react';
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
} from 'lucide-react';

// 模拟告警详情数据
const alertData = {
    id: 'ALT-2026-001',
    title: 'CPU使用率超过90%',
    content: '服务器 server-prod-001 的CPU使用率达到92%，持续5分钟。这是一个需要立即关注的问题。',
    level: 'critical',
    status: 'open',
    source: 'Prometheus',
    ci: {
        id: 1,
        name: 'server-prod-001',
        type: '物理服务器',
        ip: '192.168.1.100',
        os: 'CentOS 7.9',
        cpu: '32核',
        memory: '128GB',
    },
    alertTime: '2026-01-18 16:30:00',
    createTime: '2026-01-18 16:30:05',
};

// 智能分析结果
const analysisResult = {
    summary: 'CPU使用率异常升高，可能由应用负载增加或存在性能问题的进程导致。建议立即排查高CPU占用进程。',
    rootCauses: [
        { cause: '应用负载增加', probability: 0.45 },
        { cause: '存在死循环或性能问题的代码', probability: 0.30 },
        { cause: '后台任务占用过多资源', probability: 0.15 },
        { cause: '系统被入侵', probability: 0.10 },
    ],
    impact: '可能影响该服务器上运行的所有应用服务，导致响应变慢或服务不可用。',
    suggestedActions: [
        '使用 top 或 htop 命令查看高CPU占用进程',
        '检查应用日志是否有异常',
        '考虑临时扩容或负载均衡',
        '排查是否有未授权的进程运行',
    ],
    riskLevel: 'high',
    confidence: 0.85,
};

// 推荐方案
const solutions = [
    {
        id: 1,
        title: 'CPU使用率过高处理方案',
        content: '1. 使用 top -c 命令查看CPU占用最高的进程\n2. 使用 strace 或 perf 分析进程行为\n3. 检查应用日志...',
        source: '运维知识库',
        score: 0.92,
    },
    {
        id: 2,
        title: 'Linux服务器性能优化指南',
        content: '系统性的服务器性能优化方法，包括CPU、内存、IO等方面的优化建议...',
        source: '最佳实践文档',
        score: 0.85,
    },
    {
        id: 3,
        title: '应用负载问题排查手册',
        content: '针对应用负载异常的排查步骤和解决方案...',
        source: '故障处理手册',
        score: 0.78,
    },
];

// 关联性能数据
const performanceData = [
    { metric: 'CPU使用率', value: '92%', trend: 'up', color: 'error' },
    { metric: '内存使用率', value: '65%', trend: 'stable', color: 'warning' },
    { metric: '磁盘IO', value: '45MB/s', trend: 'up', color: 'primary' },
    { metric: '网络流量', value: '128Mbps', trend: 'stable', color: 'success' },
];

// 关联日志
const relatedLogs = [
    { time: '16:29:55', level: 'ERROR', message: 'Connection pool exhausted, waiting for available connection...' },
    { time: '16:29:58', level: 'WARN', message: 'Request processing time exceeded threshold: 5000ms' },
    { time: '16:30:02', level: 'ERROR', message: 'Database query timeout after 30s' },
    { time: '16:30:05', level: 'WARN', message: 'High CPU load detected, current: 92%' },
];

export default function AlertDetailPage({ params }: { params: { id: string } }) {
    const [analyzing, setAnalyzing] = useState(false);

    const handleReanalyze = async () => {
        setAnalyzing(true);
        await new Promise((r) => setTimeout(r, 2000));
        setAnalyzing(false);
    };

    const levelConfig = {
        critical: { label: '紧急', className: 'alert-critical', icon: AlertTriangle },
        warning: { label: '警告', className: 'alert-warning', icon: Clock },
        info: { label: '信息', className: 'alert-info', icon: CheckCircle },
    };

    const level = levelConfig[alertData.level as keyof typeof levelConfig];
    const LevelIcon = level.icon;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 面包屑 */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Link href="/alerts" className="hover:text-primary flex items-center gap-1">
                    <ArrowLeft className="h-4 w-4" />
                    告警列表
                </Link>
                <ChevronRight className="h-4 w-4" />
                <span className="text-foreground">{alertData.id}</span>
            </div>

            {/* 告警标题栏 */}
            <div className="card p-6">
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-lg ${level.className}`}>
                            <LevelIcon className="h-6 w-6" />
                        </div>
                        <div>
                            <div className="flex items-center gap-3">
                                <h1 className="text-xl font-bold text-foreground">{alertData.title}</h1>
                                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${level.className}`}>
                                    {level.label}
                                </span>
                            </div>
                            <p className="text-muted-foreground mt-2">{alertData.content}</p>
                            <div className="flex items-center gap-6 mt-4 text-sm text-muted-foreground">
                                <span className="flex items-center gap-1">
                                    <Clock className="h-4 w-4" />
                                    {alertData.alertTime}
                                </span>
                                <span className="flex items-center gap-1">
                                    <Server className="h-4 w-4" />
                                    {alertData.ci.name}
                                </span>
                                <span className="flex items-center gap-1">
                                    <Database className="h-4 w-4" />
                                    {alertData.source}
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
                        <div className="p-6 space-y-6">
                            {/* 摘要 */}
                            <div>
                                <h3 className="text-sm font-medium text-muted-foreground mb-2">问题摘要</h3>
                                <p className="text-foreground">{analysisResult.summary}</p>
                            </div>

                            {/* 可能原因 */}
                            <div>
                                <h3 className="text-sm font-medium text-muted-foreground mb-3">可能原因</h3>
                                <div className="space-y-2">
                                    {analysisResult.rootCauses.map((cause, index) => (
                                        <div key={index} className="flex items-center gap-3">
                                            <div className="flex-1">
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className="text-sm text-foreground">{cause.cause}</span>
                                                    <span className="text-sm text-muted-foreground">
                                                        {Math.round(cause.probability * 100)}%
                                                    </span>
                                                </div>
                                                <div className="h-2 bg-muted rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-primary rounded-full transition-all"
                                                        style={{ width: `${cause.probability * 100}%` }}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* 影响范围 */}
                            <div>
                                <h3 className="text-sm font-medium text-muted-foreground mb-2">影响范围</h3>
                                <p className="text-foreground">{analysisResult.impact}</p>
                            </div>

                            {/* 建议措施 */}
                            <div>
                                <h3 className="text-sm font-medium text-muted-foreground mb-3">建议措施</h3>
                                <ol className="space-y-2">
                                    {analysisResult.suggestedActions.map((action, index) => (
                                        <li key={index} className="flex items-start gap-2 text-foreground">
                                            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary/10 text-primary text-xs font-medium shrink-0 mt-0.5">
                                                {index + 1}
                                            </span>
                                            {action}
                                        </li>
                                    ))}
                                </ol>
                            </div>

                            {/* 置信度 */}
                            <div className="pt-4 border-t border-border flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">分析置信度</span>
                                <span className="text-sm font-medium text-primary">
                                    {Math.round(analysisResult.confidence * 100)}%
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 推荐方案 */}
                    <div className="card">
                        <div className="p-4 border-b border-border flex items-center gap-2">
                            <Lightbulb className="h-5 w-5 text-accent" />
                            <h2 className="font-semibold text-foreground">推荐处理方案</h2>
                        </div>
                        <div className="divide-y divide-border">
                            {solutions.map((solution) => (
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
                                                {Math.round(solution.score * 100)}%
                                            </div>
                                            <div className="text-xs text-muted-foreground">匹配度</div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* 关联日志 */}
                    <div className="card">
                        <div className="p-4 border-b border-border flex items-center gap-2">
                            <FileText className="h-5 w-5 text-muted-foreground" />
                            <h2 className="font-semibold text-foreground">关联日志</h2>
                        </div>
                        <div className="p-4 font-mono text-sm bg-dark-bg rounded-b-lg overflow-x-auto">
                            {relatedLogs.map((log, index) => (
                                <div key={index} className="flex gap-4 py-1">
                                    <span className="text-muted-foreground shrink-0">{log.time}</span>
                                    <span
                                        className={`shrink-0 ${log.level === 'ERROR'
                                                ? 'text-error'
                                                : log.level === 'WARN'
                                                    ? 'text-warning'
                                                    : 'text-muted-foreground'
                                            }`}
                                    >
                                        [{log.level}]
                                    </span>
                                    <span className="text-foreground">{log.message}</span>
                                </div>
                            ))}
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
                                { label: '名称', value: alertData.ci.name },
                                { label: '类型', value: alertData.ci.type },
                                { label: 'IP地址', value: alertData.ci.ip },
                                { label: '操作系统', value: alertData.ci.os },
                                { label: 'CPU', value: alertData.ci.cpu },
                                { label: '内存', value: alertData.ci.memory },
                            ].map((item) => (
                                <div key={item.label} className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">{item.label}</span>
                                    <span className="text-foreground">{item.value}</span>
                                </div>
                            ))}
                            <Link
                                href={`/cmdb/${alertData.ci.id}`}
                                className="block pt-3 border-t border-border text-sm text-primary hover:underline"
                            >
                                查看配置项详情 →
                            </Link>
                        </div>
                    </div>

                    {/* 实时性能 */}
                    <div className="card">
                        <div className="p-4 border-b border-border flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-muted-foreground" />
                            <h2 className="font-semibold text-foreground">实时性能</h2>
                        </div>
                        <div className="p-4 space-y-4">
                            {performanceData.map((item) => (
                                <div key={item.metric}>
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm text-muted-foreground">{item.metric}</span>
                                        <span className={`text-sm font-medium text-${item.color}`}>
                                            {item.value}
                                        </span>
                                    </div>
                                    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className={`h-full bg-${item.color} rounded-full`}
                                            style={{
                                                width:
                                                    item.metric === 'CPU使用率'
                                                        ? '92%'
                                                        : item.metric === '内存使用率'
                                                            ? '65%'
                                                            : '45%',
                                            }}
                                        />
                                    </div>
                                </div>
                            ))}
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
