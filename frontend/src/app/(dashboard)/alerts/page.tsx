'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    AlertTriangle,
    CheckCircle,
    ChevronDown,
    Clock,
    Filter,
    RefreshCw,
    Search,
    Loader2,
} from 'lucide-react';
import { getAlerts, Alert } from '@/lib/api';
import { toast } from 'sonner';

const levelConfig = {
    critical: {
        label: '紧急',
        className: 'bg-error/10 text-error border-error/30',
        icon: AlertTriangle,
    },
    warning: {
        label: '警告',
        className: 'bg-warning/10 text-warning border-warning/30',
        icon: Clock,
    },
    info: {
        label: '信息',
        className: 'bg-primary/10 text-primary border-primary/30',
        icon: CheckCircle,
    },
};

const statusConfig = {
    open: { label: '待处理', className: 'bg-error/10 text-error' },
    acknowledged: { label: '已确认', className: 'bg-warning/10 text-warning' },
    resolved: { label: '已解决', className: 'bg-success/10 text-success' },
};

export default function AlertsPage() {
    const [selectedLevel, setSelectedLevel] = useState<string>('all');
    const [selectedStatus, setSelectedStatus] = useState<string>('all');
    const [searchQuery, setSearchQuery] = useState('');

    // API Data state
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        total: 0,
        critical: 0,
        open: 0,
        resolved: 0
    });

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const params: any = {
                page: 1,
                size: 100, // Handle pagination properly in real app, simplified here
            };

            if (selectedLevel !== 'all') params.level = selectedLevel;
            if (selectedStatus !== 'all') params.status = selectedStatus;
            if (searchQuery) params.keyword = searchQuery;

            const res = await getAlerts(params);

            setAlerts(res.items);

            // Calculate stats from current batch (or fetch from separate stats API if available)
            // Ideally backend provides stats, but for now we calculate from the list or separate calls
            // Simplified: just use list length for demo or implement getStats API later
            setStats({
                total: res.total,
                critical: res.items.filter(a => a.level === 'critical').length, // This is just for current page, ideally separate API
                open: res.items.filter(a => a.status === 'open').length,
                resolved: res.items.filter(a => a.status === 'resolved').length
            });

        } catch (error) {
            console.error('Failed to fetch alerts:', error);
            toast.error('获取告警列表失败');
        } finally {
            setLoading(false);
        }
    };

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchAlerts();
        }, 300);
        return () => clearTimeout(timer);
    }, [selectedLevel, selectedStatus, searchQuery]);

    const handleRefresh = () => {
        fetchAlerts();
    };

    // Format date helper
    const formatDate = (dateString: string) => {
        try {
            return new Date(dateString).toLocaleString('zh-CN');
        } catch {
            return dateString;
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 页面标题 */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">告警中心</h1>
                    <p className="text-muted-foreground mt-1">
                        管理和分析系统告警
                    </p>
                </div>
                <button
                    onClick={handleRefresh}
                    disabled={loading}
                    className="btn-primary flex items-center gap-2"
                >
                    <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    刷新
                </button>
            </div>

            {/* 统计概览 - 注意：这里只是当前筛选结果的统计，真实场景应该请求后端统计接口 */}
            <div className="grid grid-cols-4 gap-4">
                {[
                    { label: '全部告警', value: stats.total, color: 'primary' },
                    {
                        label: '紧急',
                        value: stats.critical,
                        color: 'error',
                    },
                    {
                        label: '待处理',
                        value: stats.open,
                        color: 'warning',
                    },
                    {
                        label: '已解决',
                        value: stats.resolved,
                        color: 'success',
                    },
                ].map((stat) => (
                    <div
                        key={stat.label}
                        className="card p-4 cursor-pointer hover:border-primary/50 transition-colors"
                    >
                        <p className="text-sm text-muted-foreground">{stat.label}</p>
                        <p className={`text-2xl font-bold text-${stat.color}`}>{stat.value}</p>
                    </div>
                ))}
            </div>

            {/* 筛选栏 */}
            <div className="card p-4">
                <div className="flex items-center gap-4">
                    <div className="relative flex-1 max-w-sm">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="搜索告警标题或配置项..."
                            className="input pl-10"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>

                    <div className="flex items-center gap-2">
                        <Filter className="h-4 w-4 text-muted-foreground" />
                        <select
                            value={selectedLevel}
                            onChange={(e) => setSelectedLevel(e.target.value)}
                            className="input w-32"
                        >
                            <option value="all">全部级别</option>
                            <option value="critical">紧急</option>
                            <option value="warning">警告</option>
                            <option value="info">信息</option>
                        </select>

                        <select
                            value={selectedStatus}
                            onChange={(e) => setSelectedStatus(e.target.value)}
                            className="input w-32"
                        >
                            <option value="all">全部状态</option>
                            <option value="open">待处理</option>
                            <option value="acknowledged">已确认</option>
                            <option value="resolved">已解决</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* 告警列表 */}
            <div className="card overflow-hidden min-h-[400px]">
                {loading && alerts.length === 0 ? (
                    <div className="flex items-center justify-center h-64">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </div>
                ) : (
                    <table className="w-full">
                        <thead className="bg-muted/50">
                            <tr>
                                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                    级别
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                    告警信息
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                    配置项
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                    来源
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                    状态
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                    时间
                                </th>
                                <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                    操作
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {alerts.map((alert) => {
                                const level = levelConfig[alert.level as keyof typeof levelConfig] || levelConfig.info;
                                const status = statusConfig[alert.status as keyof typeof statusConfig] || statusConfig.open;
                                const LevelIcon = level.icon;

                                return (
                                    <tr
                                        key={alert.alert_id}
                                        className="hover:bg-accent/5 transition-colors cursor-pointer"
                                    >
                                        <td className="px-4 py-4">
                                            <span
                                                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${level.className}`}
                                            >
                                                <LevelIcon className="h-3.5 w-3.5" />
                                                {level.label}
                                            </span>
                                        </td>
                                        <td className="px-4 py-4">
                                            <div>
                                                <p className="font-medium text-foreground">{alert.title}</p>
                                                <p className="text-sm text-muted-foreground mt-0.5 line-clamp-1">
                                                    {alert.content}
                                                </p>
                                            </div>
                                        </td>
                                        <td className="px-4 py-4">
                                            <div>
                                                <p className="text-foreground">{alert.ci_name || alert.tags?.ci_identifier || '-'}</p>
                                                <p className="text-sm text-muted-foreground">{alert.tags?.ci_type || '-'}</p>
                                            </div>
                                        </td>
                                        <td className="px-4 py-4 text-muted-foreground">{alert.source || 'Unknown'}</td>
                                        <td className="px-4 py-4">
                                            <span
                                                className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                                            >
                                                {status.label}
                                            </span>
                                        </td>
                                        <td className="px-4 py-4 text-sm text-muted-foreground">
                                            {formatDate(alert.alert_time)}
                                        </td>
                                        <td className="px-4 py-4">
                                            <Link
                                                href={`/alerts/${alert.alert_id}`}
                                                className="text-primary hover:underline text-sm"
                                            >
                                                查看详情
                                            </Link>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                )}

                {!loading && alerts.length === 0 && (
                    <div className="p-8 text-center text-muted-foreground">
                        没有找到匹配的告警
                    </div>
                )}
            </div>
        </div>
    );
}
