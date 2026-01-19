'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
    AlertTriangle,
    ArrowLeft,
    ChevronRight,
    Clock,
    Database,
    Edit,
    Network,
    Server,
    Trash2,
} from 'lucide-react';

// 模拟配置项详情
const ciDetail = {
    id: 1,
    name: 'server-prod-001',
    typeCode: 'server',
    typeName: '物理服务器',
    identifier: 'SRV-001',
    status: 'active',
    attributes: {
        ip: '192.168.1.100',
        hostname: 'server-prod-001.example.com',
        os: 'CentOS 7.9',
        cpu: '32核',
        memory: '128GB',
        disk: '2TB SSD',
        location: '数据中心A',
        rack: 'A-01-05',
    },
    createdAt: '2026-01-01 10:00:00',
    updatedAt: '2026-01-18 15:30:00',
};

// 关系配置项
const relationships = {
    upstream: [
        { id: 10, name: 'router-core-001', type: '网络设备', relType: 'connects' },
    ],
    downstream: [
        { id: 20, name: 'app-web-001', type: '应用服务', relType: 'runs_on' },
        { id: 21, name: 'app-api-001', type: '应用服务', relType: 'runs_on' },
        { id: 22, name: 'db-slave-001', type: '数据库', relType: 'backup' },
    ],
};

// 关联告警
const relatedAlerts = [
    {
        id: 'ALT-001',
        title: 'CPU使用率超过90%',
        level: 'critical',
        time: '5分钟前',
    },
    {
        id: 'ALT-002',
        title: '内存使用率告警',
        level: 'warning',
        time: '1小时前',
    },
];

const statusConfig = {
    active: { label: '运行中', className: 'bg-success/10 text-success' },
    inactive: { label: '已停用', className: 'bg-muted text-muted-foreground' },
    maintenance: { label: '维护中', className: 'bg-warning/10 text-warning' },
    error: { label: '故障', className: 'bg-error/10 text-error' },
};

export default function CIDetailPage({ params }: { params: { id: string } }) {
    const [activeTab, setActiveTab] = useState<'attributes' | 'relationships' | 'alerts'>('attributes');
    const status = statusConfig[ciDetail.status as keyof typeof statusConfig];

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 面包屑 */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Link href="/cmdb" className="hover:text-primary flex items-center gap-1">
                    <ArrowLeft className="h-4 w-4" />
                    配置项列表
                </Link>
                <ChevronRight className="h-4 w-4" />
                <span className="text-foreground">{ciDetail.name}</span>
            </div>

            {/* 配置项标题栏 */}
            <div className="card p-6">
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                        <div className="p-3 rounded-lg bg-primary/10 text-primary">
                            <Server className="h-8 w-8" />
                        </div>
                        <div>
                            <div className="flex items-center gap-3">
                                <h1 className="text-xl font-bold text-foreground">{ciDetail.name}</h1>
                                <span
                                    className={`px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                                >
                                    {status.label}
                                </span>
                            </div>
                            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                                <span>类型: {ciDetail.typeName}</span>
                                <span>标识: {ciDetail.identifier}</span>
                                <span>创建于: {ciDetail.createdAt}</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button className="btn-outline flex items-center gap-2">
                            <Edit className="h-4 w-4" />
                            编辑
                        </button>
                        <button className="btn-outline text-error hover:bg-error/10 flex items-center gap-2">
                            <Trash2 className="h-4 w-4" />
                            删除
                        </button>
                    </div>
                </div>
            </div>

            {/* 标签页 */}
            <div className="card">
                <div className="border-b border-border">
                    <div className="flex gap-1 p-1">
                        {[
                            { key: 'attributes', label: '属性信息' },
                            { key: 'relationships', label: '关系拓扑' },
                            { key: 'alerts', label: '关联告警' },
                        ].map((tab) => (
                            <button
                                key={tab.key}
                                onClick={() => setActiveTab(tab.key as typeof activeTab)}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab.key
                                        ? 'bg-primary/10 text-primary'
                                        : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                                    }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 属性信息 */}
                {activeTab === 'attributes' && (
                    <div className="p-6">
                        <div className="grid grid-cols-2 gap-6">
                            {Object.entries(ciDetail.attributes).map(([key, value]) => (
                                <div key={key} className="space-y-1">
                                    <label className="text-sm text-muted-foreground">{key}</label>
                                    <div className="text-foreground font-medium">{value}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 关系拓扑 */}
                {activeTab === 'relationships' && (
                    <div className="p-6 space-y-6">
                        {/* 上游依赖 */}
                        <div>
                            <h3 className="text-sm font-medium text-muted-foreground mb-3">
                                上游依赖 ({relationships.upstream.length})
                            </h3>
                            <div className="space-y-2">
                                {relationships.upstream.map((rel) => (
                                    <Link
                                        key={rel.id}
                                        href={`/cmdb/${rel.id}`}
                                        className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-primary/50 transition-colors cursor-pointer"
                                    >
                                        <Network className="h-5 w-5 text-primary" />
                                        <div className="flex-1">
                                            <div className="font-medium text-foreground">{rel.name}</div>
                                            <div className="text-sm text-muted-foreground">{rel.type}</div>
                                        </div>
                                        <div className="text-xs px-2 py-1 bg-muted rounded">
                                            {rel.relType}
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        </div>

                        {/* 下游依赖 */}
                        <div>
                            <h3 className="text-sm font-medium text-muted-foreground mb-3">
                                下游依赖 ({relationships.downstream.length})
                            </h3>
                            <div className="space-y-2">
                                {relationships.downstream.map((rel) => (
                                    <Link
                                        key={rel.id}
                                        href={`/cmdb/${rel.id}`}
                                        className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-primary/50 transition-colors cursor-pointer"
                                    >
                                        <Database className="h-5 w-5 text-accent" />
                                        <div className="flex-1">
                                            <div className="font-medium text-foreground">{rel.name}</div>
                                            <div className="text-sm text-muted-foreground">{rel.type}</div>
                                        </div>
                                        <div className="text-xs px-2 py-1 bg-muted rounded">
                                            {rel.relType}
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        </div>

                        <div className="pt-4 border-t border-border">
                            <Link
                                href="/cmdb/topology"
                                className="btn-primary w-full justify-center"
                            >
                                <Network className="h-4 w-4 mr-2" />
                                查看完整拓扑图
                            </Link>
                        </div>
                    </div>
                )}

                {/* 关联告警 */}
                {activeTab === 'alerts' && (
                    <div className="p-6">
                        {relatedAlerts.length > 0 ? (
                            <div className="space-y-2">
                                {relatedAlerts.map((alert) => (
                                    <Link
                                        key={alert.id}
                                        href={`/alerts/${alert.id}`}
                                        className="flex items-center gap-3 p-4 rounded-lg border border-border hover:border-primary/50 transition-colors cursor-pointer"
                                    >
                                        <div
                                            className={`p-2 rounded-lg ${alert.level === 'critical'
                                                    ? 'alert-critical'
                                                    : 'alert-warning'
                                                }`}
                                        >
                                            {alert.level === 'critical' ? (
                                                <AlertTriangle className="h-5 w-5" />
                                            ) : (
                                                <Clock className="h-5 w-5" />
                                            )}
                                        </div>
                                        <div className="flex-1">
                                            <div className="font-medium text-foreground">{alert.title}</div>
                                            <div className="text-sm text-muted-foreground">{alert.id}</div>
                                        </div>
                                        <div className="text-sm text-muted-foreground">{alert.time}</div>
                                    </Link>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8 text-muted-foreground">
                                暂无关联告警
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
