'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
    Database,
    Filter,
    Network,
    Plus,
    RefreshCw,
    Search,
    Server,
} from 'lucide-react';

// 模拟配置项数据
const mockCIs = [
    {
        id: 1,
        name: 'server-prod-001',
        typeCode: 'server',
        typeName: '物理服务器',
        identifier: 'SRV-001',
        status: 'active',
        attributes: {
            ip: '192.168.1.100',
            os: 'CentOS 7.9',
            cpu: '32核',
            memory: '128GB',
        },
        updatedAt: '2026-01-18 15:30:00',
    },
    {
        id: 2,
        name: 'db-master-001',
        typeCode: 'database',
        typeName: '数据库',
        identifier: 'DB-001',
        status: 'active',
        attributes: {
            ip: '192.168.1.101',
            dbType: 'MySQL 8.0',
            version: '8.0.32',
        },
        updatedAt: '2026-01-18 14:20:00',
    },
    {
        id: 3,
        name: 'router-core-001',
        typeCode: 'network',
        typeName: '网络设备',
        identifier: 'NET-001',
        status: 'active',
        attributes: {
            ip: '192.168.1.1',
            model: 'Cisco ASR 9000',
            ports: '48',
        },
        updatedAt: '2026-01-17 10:15:00',
    },
    {
        id: 4,
        name: 'app-web-001',
        typeCode: 'application',
        typeName: '应用服务',
        identifier: 'APP-001',
        status: 'active',
        attributes: {
            port: '8080',
            version: 'v2.3.1',
            framework: 'Spring Boot',
        },
        updatedAt: '2026-01-16 18:45:00',
    },
];

const ciTypeIcons: Record<string, typeof Server> = {
    server: Server,
    database: Database,
    network: Network,
    application: Server,
};

const statusConfig = {
    active: { label: '运行中', className: 'bg-success/10 text-success' },
    inactive: { label: '已停用', className: 'bg-muted text-muted-foreground' },
    maintenance: { label: '维护中', className: 'bg-warning/10 text-warning' },
    error: { label: '故障', className: 'bg-error/10 text-error' },
};

export default function CMDBPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedType, setSelectedType] = useState<string>('all');
    const [selectedStatus, setSelectedStatus] = useState<string>('all');
    const [showAddModal, setShowAddModal] = useState(false);

    const filteredCIs = mockCIs.filter((ci) => {
        if (selectedType !== 'all' && ci.typeCode !== selectedType) return false;
        if (selectedStatus !== 'all' && ci.status !== selectedStatus) return false;
        if (
            searchQuery &&
            !ci.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
            !ci.identifier.toLowerCase().includes(searchQuery.toLowerCase())
        )
            return false;
        return true;
    });

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 页面标题 */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">CMDB 配置管理</h1>
                    <p className="text-muted-foreground mt-1">管理IT基础设施配置项</p>
                </div>
                <div className="flex gap-2">
                    <Link href="/cmdb/topology" className="btn-outline flex items-center gap-2">
                        <Network className="h-4 w-4" />
                        拓扑图
                    </Link>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="btn-primary flex items-center gap-2"
                    >
                        <Plus className="h-4 w-4" />
                        新增配置项
                    </button>
                </div>
            </div>

            {/* 统计概览 */}
            <div className="grid grid-cols-4 gap-4">
                {[
                    { label: '全部配置项', value: mockCIs.length, color: 'primary' },
                    {
                        label: '物理服务器',
                        value: mockCIs.filter((c) => c.typeCode === 'server').length,
                        color: 'accent',
                    },
                    {
                        label: '数据库',
                        value: mockCIs.filter((c) => c.typeCode === 'database').length,
                        color: 'success',
                    },
                    {
                        label: '运行中',
                        value: mockCIs.filter((c) => c.status === 'active').length,
                        color: 'warning',
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
                            placeholder="搜索配置项名称或标识..."
                            className="input pl-10"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>

                    <div className="flex items-center gap-2">
                        <Filter className="h-4 w-4 text-muted-foreground" />
                        <select
                            value={selectedType}
                            onChange={(e) => setSelectedType(e.target.value)}
                            className="input w-40"
                        >
                            <option value="all">全部类型</option>
                            <option value="server">物理服务器</option>
                            <option value="database">数据库</option>
                            <option value="network">网络设备</option>
                            <option value="application">应用服务</option>
                        </select>

                        <select
                            value={selectedStatus}
                            onChange={(e) => setSelectedStatus(e.target.value)}
                            className="input w-32"
                        >
                            <option value="all">全部状态</option>
                            <option value="active">运行中</option>
                            <option value="inactive">已停用</option>
                            <option value="maintenance">维护中</option>
                            <option value="error">故障</option>
                        </select>

                        <button className="btn-ghost flex items-center gap-1">
                            <RefreshCw className="h-4 w-4" />
                            刷新
                        </button>
                    </div>
                </div>
            </div>

            {/* 配置项列表 */}
            <div className="card overflow-hidden">
                <table className="w-full">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                配置项名称
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                类型
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                标识符
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                状态
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                关键属性
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                更新时间
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                操作
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {filteredCIs.map((ci) => {
                            const Icon = ciTypeIcons[ci.typeCode] || Server;
                            const status = statusConfig[ci.status as keyof typeof statusConfig];

                            return (
                                <tr
                                    key={ci.id}
                                    className="hover:bg-accent/5 transition-colors cursor-pointer"
                                >
                                    <td className="px-4 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 rounded-lg bg-primary/10 text-primary">
                                                <Icon className="h-5 w-5" />
                                            </div>
                                            <Link
                                                href={`/cmdb/${ci.id}`}
                                                className="font-medium text-foreground hover:text-primary"
                                            >
                                                {ci.name}
                                            </Link>
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 text-muted-foreground">{ci.typeName}</td>
                                    <td className="px-4 py-4">
                                        <code className="px-2 py-1 bg-muted rounded text-sm text-foreground">
                                            {ci.identifier}
                                        </code>
                                    </td>
                                    <td className="px-4 py-4">
                                        <span
                                            className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                                        >
                                            {status.label}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4">
                                        <div className="text-sm space-y-0.5">
                                            {Object.entries(ci.attributes)
                                                .slice(0, 2)
                                                .map(([key, value]) => (
                                                    <div key={key} className="text-muted-foreground">
                                                        {key}: <span className="text-foreground">{value}</span>
                                                    </div>
                                                ))}
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground">
                                        {ci.updatedAt}
                                    </td>
                                    <td className="px-4 py-4">
                                        <Link
                                            href={`/cmdb/${ci.id}`}
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

                {filteredCIs.length === 0 && (
                    <div className="p-8 text-center text-muted-foreground">
                        没有找到匹配的配置项
                    </div>
                )}
            </div>

            {/* 新增配置项模态框 */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-lg animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-4">新增配置项</h2>
                        <form className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    配置项名称 <span className="text-error">*</span>
                                </label>
                                <input
                                    type="text"
                                    placeholder="如: server-prod-002"
                                    className="input w-full"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    配置项类型 <span className="text-error">*</span>
                                </label>
                                <select className="input w-full">
                                    <option value="">请选择类型</option>
                                    <option value="server">物理服务器</option>
                                    <option value="database">数据库</option>
                                    <option value="network">网络设备</option>
                                    <option value="application">应用服务</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    标识符
                                </label>
                                <input
                                    type="text"
                                    placeholder="如: SRV-002"
                                    className="input w-full"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    IP 地址
                                </label>
                                <input
                                    type="text"
                                    placeholder="如: 192.168.1.100"
                                    className="input w-full"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    描述
                                </label>
                                <textarea
                                    placeholder="配置项描述信息..."
                                    className="input w-full min-h-[80px] resize-none"
                                />
                            </div>
                        </form>
                        <div className="flex gap-3 pt-6">
                            <button
                                onClick={() => setShowAddModal(false)}
                                className="btn-outline flex-1"
                            >
                                取消
                            </button>
                            <button className="btn-primary flex-1">创建配置项</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
