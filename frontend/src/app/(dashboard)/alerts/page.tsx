'use client';

import { useState } from 'react';
import {
    AlertTriangle,
    CheckCircle,
    ChevronDown,
    Clock,
    Filter,
    RefreshCw,
    Search,
} from 'lucide-react';

// 模拟告警数据
const mockAlerts = [
    {
        id: 'ALT-2026-001',
        title: 'CPU使用率超过90%',
        content: '服务器 server-prod-001 的CPU使用率达到92%，持续5分钟',
        level: 'critical',
        status: 'open',
        source: 'Prometheus',
        ci: 'server-prod-001',
        ciType: '物理服务器',
        alertTime: '2026-01-18 16:30:00',
    },
    {
        id: 'ALT-2026-002',
        title: '内存使用率告警',
        content: '服务器 server-prod-003 内存使用率达到85%',
        level: 'warning',
        status: 'acknowledged',
        source: 'Zabbix',
        ci: 'server-prod-003',
        ciType: '物理服务器',
        alertTime: '2026-01-18 16:15:00',
    },
    {
        id: 'ALT-2026-003',
        title: '磁盘空间不足',
        content: '数据库服务器 db-master-001 磁盘使用率超过90%',
        level: 'warning',
        status: 'open',
        source: 'Prometheus',
        ci: 'db-master-001',
        ciType: '数据库',
        alertTime: '2026-01-18 16:00:00',
    },
    {
        id: 'ALT-2026-004',
        title: '网络延迟异常',
        content: '核心路由器网络延迟超过100ms',
        level: 'info',
        status: 'resolved',
        source: 'SNMP',
        ci: 'router-core-001',
        ciType: '网络设备',
        alertTime: '2026-01-18 15:30:00',
    },
];

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

    const filteredAlerts = mockAlerts.filter((alert) => {
        if (selectedLevel !== 'all' && alert.level !== selectedLevel) return false;
        if (selectedStatus !== 'all' && alert.status !== selectedStatus) return false;
        if (
            searchQuery &&
            !alert.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
            !alert.ci.toLowerCase().includes(searchQuery.toLowerCase())
        )
            return false;
        return true;
    });

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
                <button className="btn-primary flex items-center gap-2">
                    <RefreshCw className="h-4 w-4" />
                    刷新
                </button>
            </div>

            {/* 统计概览 */}
            <div className="grid grid-cols-4 gap-4">
                {[
                    { label: '全部告警', value: mockAlerts.length, color: 'primary' },
                    {
                        label: '紧急',
                        value: mockAlerts.filter((a) => a.level === 'critical').length,
                        color: 'error',
                    },
                    {
                        label: '待处理',
                        value: mockAlerts.filter((a) => a.status === 'open').length,
                        color: 'warning',
                    },
                    {
                        label: '已解决',
                        value: mockAlerts.filter((a) => a.status === 'resolved').length,
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
            <div className="card overflow-hidden">
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
                        {filteredAlerts.map((alert) => {
                            const level = levelConfig[alert.level as keyof typeof levelConfig];
                            const status = statusConfig[alert.status as keyof typeof statusConfig];
                            const LevelIcon = level.icon;

                            return (
                                <tr
                                    key={alert.id}
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
                                            <p className="text-foreground">{alert.ci}</p>
                                            <p className="text-sm text-muted-foreground">{alert.ciType}</p>
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 text-muted-foreground">{alert.source}</td>
                                    <td className="px-4 py-4">
                                        <span
                                            className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                                        >
                                            {status.label}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground">
                                        {alert.alertTime}
                                    </td>
                                    <td className="px-4 py-4">
                                        <a
                                            href={`/alerts/${alert.id}`}
                                            className="text-primary hover:underline text-sm"
                                        >
                                            查看详情
                                        </a>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>

                {filteredAlerts.length === 0 && (
                    <div className="p-8 text-center text-muted-foreground">
                        没有找到匹配的告警
                    </div>
                )}
            </div>
        </div>
    );
}
