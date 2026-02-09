'use client';

import { useEffect, useState } from 'react';
import {
    AlertTriangle,
    ArrowDown,
    ArrowUp,
    Bell,
    BookOpen,
    CheckCircle,
    Clock,
    Database,
    TrendingUp,
    Loader2,
} from 'lucide-react';
import { getDashboardSummary, DashboardSummary, RecentAlert } from '@/lib/api';

// 快捷入口
const quickActions = [
    { title: '智能问答', href: '/knowledge/qa', icon: BookOpen },
    { title: '告警分析', href: '/alerts', icon: Bell },
    { title: '配置查询', href: '/cmdb', icon: Database },
];

export default function DashboardPage() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<DashboardSummary | null>(null);

    useEffect(() => {
        async function fetchData() {
            try {
                setLoading(true);
                setError(null);
                const summary = await getDashboardSummary();
                setData(summary);
            } catch (err) {
                console.error('获取仪表盘数据失败:', err);
                setError('加载数据失败，请稍后重试');
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    // 构建统计卡片数据
    const stats = data ? [
        {
            title: '待处理告警',
            value: data.pending_alerts,
            change: data.pending_alerts_change,
            trend: data.pending_alerts_change.startsWith('-') ? 'down' : 'up',
            icon: Bell,
            color: 'error',
        },
        {
            title: '知识库文档',
            value: data.document_count,
            change: data.document_change,
            trend: data.document_change.startsWith('-') ? 'down' : 'up',
            icon: BookOpen,
            color: 'primary',
        },
        {
            title: '配置项总数',
            value: data.ci_count,
            change: data.ci_change,
            trend: data.ci_change.startsWith('-') ? 'down' : 'up',
            icon: Database,
            color: 'accent',
        },
        {
            title: '今日问答',
            value: data.today_qa,
            change: data.today_qa_change,
            trend: data.today_qa_change.startsWith('-') ? 'down' : 'up',
            icon: TrendingUp,
            color: 'success',
        },
    ] : [];

    const recentAlerts: RecentAlert[] = data?.recent_alerts || [];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <span className="ml-2 text-muted-foreground">加载中...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-error mx-auto mb-4" />
                    <p className="text-error">{error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                    >
                        重试
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 页面标题 */}
            <div>
                <h1 className="text-2xl font-bold text-foreground">仪表盘</h1>
                <p className="text-muted-foreground mt-1">
                    欢迎回来，这是系统运行概览
                </p>
            </div>

            {/* 统计卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat) => {
                    const Icon = stat.icon;
                    const colorClasses = {
                        primary: 'bg-primary/10 text-primary',
                        error: 'bg-error/10 text-error',
                        accent: 'bg-accent/10 text-accent',
                        success: 'bg-success/10 text-success',
                    };

                    return (
                        <div key={stat.title} className="card p-6 cursor-pointer hover:border-primary/50 transition-colors">
                            <div className="flex items-start justify-between">
                                <div
                                    className={`p-3 rounded-lg ${colorClasses[stat.color as keyof typeof colorClasses]}`}
                                >
                                    <Icon className="h-6 w-6" />
                                </div>
                                <div
                                    className={`flex items-center gap-1 text-sm ${stat.trend === 'up' ? 'text-success' : 'text-error'
                                        }`}
                                >
                                    {stat.trend === 'up' ? (
                                        <ArrowUp className="h-4 w-4" />
                                    ) : (
                                        <ArrowDown className="h-4 w-4" />
                                    )}
                                    <span>{stat.change}</span>
                                </div>
                            </div>
                            <div className="mt-4">
                                <p className="text-3xl font-bold text-foreground">{stat.value}</p>
                                <p className="text-sm text-muted-foreground mt-1">{stat.title}</p>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 最近告警 */}
                <div className="lg:col-span-2 card">
                    <div className="p-4 border-b border-border flex items-center justify-between">
                        <h2 className="font-semibold text-foreground">最近告警</h2>
                        <a
                            href="/alerts"
                            className="text-sm text-primary hover:underline cursor-pointer"
                        >
                            查看全部
                        </a>
                    </div>
                    <div className="divide-y divide-border">
                        {recentAlerts.length === 0 ? (
                            <div className="p-8 text-center text-muted-foreground">
                                暂无告警数据
                            </div>
                        ) : (
                            recentAlerts.map((alert) => (
                                <a
                                    key={alert.id}
                                    href={`/alerts/${alert.id}`}
                                    className="p-4 flex items-center gap-4 hover:bg-accent/5 transition-colors cursor-pointer block"
                                >
                                    <div
                                        className={`p-2 rounded-lg ${alert.level === 'critical'
                                            ? 'alert-critical'
                                            : alert.level === 'warning'
                                                ? 'alert-warning'
                                                : 'alert-info'
                                            }`}
                                    >
                                        {alert.level === 'critical' ? (
                                            <AlertTriangle className="h-5 w-5" />
                                        ) : alert.level === 'warning' ? (
                                            <Clock className="h-5 w-5" />
                                        ) : (
                                            <CheckCircle className="h-5 w-5" />
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-foreground truncate">
                                            {alert.title}
                                        </p>
                                        <p className="text-sm text-muted-foreground">{alert.ci}</p>
                                    </div>
                                    <span className="text-sm text-muted-foreground whitespace-nowrap">
                                        {alert.time}
                                    </span>
                                </a>
                            ))
                        )}
                    </div>
                </div>

                {/* 快捷入口 */}
                <div className="card">
                    <div className="p-4 border-b border-border">
                        <h2 className="font-semibold text-foreground">快捷入口</h2>
                    </div>
                    <div className="p-4 space-y-3">
                        {quickActions.map((action) => {
                            const Icon = action.icon;
                            return (
                                <a
                                    key={action.title}
                                    href={action.href}
                                    className="flex items-center gap-3 p-4 rounded-lg border border-border hover:border-primary/50 hover:bg-primary/5 transition-colors cursor-pointer"
                                >
                                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                                        <Icon className="h-5 w-5" />
                                    </div>
                                    <span className="font-medium text-foreground">
                                        {action.title}
                                    </span>
                                </a>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
