'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
    Database,
    Filter,
    Network,
    Plus,
    RefreshCw,
    Search,
    Server,
    Loader2,
    Settings,
} from 'lucide-react';
import { getCIs, getCITypes, createCI, type CI, type CIType } from '@/lib/api';
import { DynamicForm } from '@/components/DynamicForm';

const statusConfig = {
    active: { label: '运行中', className: 'bg-success/10 text-success' },
    inactive: { label: '已停用', className: 'bg-muted text-muted-foreground' },
    maintenance: { label: '维护中', className: 'bg-warning/10 text-warning' },
    error: { label: '故障', className: 'bg-error/10 text-error' },
};

export default function CMDBPage() {
    const [cis, setCis] = useState<CI[]>([]);
    const [ciTypes, setCiTypes] = useState<CIType[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedType, setSelectedType] = useState<string>('all');
    const [selectedStatus, setSelectedStatus] = useState<string>('all');
    const [showAddModal, setShowAddModal] = useState(false);

    // 新增表单状态
    const [newCiData, setNewCiData] = useState({
        name: '',
        typeCode: '',
        identifier: '',
        attributes: {} as Record<string, any>
    });

    // 加载类型数据
    useEffect(() => {
        async function loadTypes() {
            try {
                const res = await getCITypes();
                setCiTypes(res.items);
            } catch (error) {
                console.error('Failed to load CI types:', error);
            }
        }
        loadTypes();
    }, []);

    // 加载配置项数据
    useEffect(() => {
        async function loadData() {
            setLoading(true);
            try {
                const res = await getCIs({
                    type_code: selectedType === 'all' ? undefined : selectedType,
                    status: selectedStatus === 'all' ? undefined : selectedStatus,
                    keyword: searchQuery || undefined,
                    page: 1,
                    size: 20
                });
                setCis(res.items);
            } catch (error) {
                console.error('Failed to load CIs:', error);
            } finally {
                setLoading(false);
            }
        }

        // 防抖
        const timer = setTimeout(loadData, 300);
        return () => clearTimeout(timer);
    }, [selectedType, selectedStatus, searchQuery]);

    const handleCreate = async () => {
        try {
            await createCI({
                type_code: newCiData.typeCode,
                name: newCiData.name,
                identifier: newCiData.identifier,
                attributes: newCiData.attributes
            });
            setShowAddModal(false);
            // 刷新列表
            const res = await getCIs();
            setCis(res.items);
            // 重置表单
            setNewCiData({ name: '', typeCode: '', identifier: '', attributes: {} });
        } catch (error) {
            alert('创建失败: ' + (error as Error).message);
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 页面标题 */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">CMDB 配置管理</h1>
                    <p className="text-muted-foreground mt-1">管理IT基础设施配置项</p>
                </div>
                <div className="flex gap-2">
                    <Link href="/cmdb/types" className="btn-outline flex items-center gap-2">
                        <Settings className="h-4 w-4" />
                        类型管理
                    </Link>
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
                    { label: '全部配置项', value: cis.length, color: 'primary' },
                    {
                        label: '物理服务器',
                        value: cis.filter((c) => c.type_code === 'server').length,
                        color: 'accent',
                    },
                    {
                        label: '数据库',
                        value: cis.filter((c) => c.type_code === 'database').length,
                        color: 'success',
                    },
                    {
                        label: '运行中',
                        value: cis.filter((c) => c.status === 'active').length,
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
                            {ciTypes.map(type => (
                                <option key={type.code} value={type.code}>{type.name}</option>
                            ))}
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

                        <button className="btn-ghost flex items-center gap-1" onClick={() => window.location.reload()}>
                            <RefreshCw className="h-4 w-4" />
                            刷新
                        </button>
                    </div>
                </div>
            </div>

            {/* 配置项列表 */}
            <div className="card overflow-hidden min-h-[400px]">
                {loading ? (
                    <div className="flex items-center justify-center h-full py-20">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </div>
                ) : (
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
                            {cis.map((ci) => {
                                const status = statusConfig[ci.status as keyof typeof statusConfig] || statusConfig.active;
                                const ciType = ciTypes.find(t => t.code === ci.type_code);

                                return (
                                    <tr
                                        key={ci.id}
                                        className="hover:bg-accent/5 transition-colors cursor-pointer"
                                    >
                                        <td className="px-4 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 rounded-lg bg-primary/10 text-primary">
                                                    <Server className="h-5 w-5" />
                                                </div>
                                                <Link
                                                    href={`/cmdb/${ci.id}`}
                                                    className="font-medium text-foreground hover:text-primary"
                                                >
                                                    {ci.name}
                                                </Link>
                                            </div>
                                        </td>
                                        <td className="px-4 py-4 text-muted-foreground">{ci.type_name || ciType?.name || ci.type_code}</td>
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
                                                {ci.attributes && Object.entries(ci.attributes)
                                                    .slice(0, 2)
                                                    .map(([key, value]) => (
                                                        <div key={key} className="text-muted-foreground">
                                                            {key}: <span className="text-foreground">{String(value)}</span>
                                                        </div>
                                                    ))}
                                            </div>
                                        </td>
                                        <td className="px-4 py-4 text-sm text-muted-foreground">
                                            {ci.updated_at ? new Date(ci.updated_at).toLocaleString() : '-'}
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
                )}

                {!loading && cis.length === 0 && (
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
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    配置项类型 <span className="text-error">*</span>
                                </label>
                                <select
                                    className="input w-full"
                                    value={newCiData.typeCode}
                                    onChange={(e) => setNewCiData({ ...newCiData, typeCode: e.target.value })}
                                >
                                    <option value="">请选择类型</option>
                                    {ciTypes.map(type => (
                                        <option key={type.code} value={type.code}>{type.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    配置项名称 <span className="text-error">*</span>
                                </label>
                                <input
                                    type="text"
                                    placeholder="如: server-prod-002"
                                    className="input w-full"
                                    value={newCiData.name}
                                    onChange={(e) => setNewCiData({ ...newCiData, name: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    标识符
                                </label>
                                <input
                                    type="text"
                                    placeholder="如: SRV-002"
                                    className="input w-full"
                                    value={newCiData.identifier}
                                    onChange={(e) => setNewCiData({ ...newCiData, identifier: e.target.value })}
                                />
                            </div>

                            {/* 动态属性表单 */}
                            {newCiData.typeCode && (
                                <div className="border-t border-border pt-4 mt-2">
                                    <h3 className="text-sm font-medium mb-3">类型属性</h3>
                                    <DynamicForm
                                        schema={ciTypes.find(t => t.code === newCiData.typeCode)?.attribute_schema}
                                        initialValues={newCiData.attributes}
                                        onChange={(values) => setNewCiData(prev => ({ ...prev, attributes: values }))}
                                    />
                                </div>
                            )}
                        </div>
                        <div className="flex gap-3 pt-6">
                            <button
                                onClick={() => setShowAddModal(false)}
                                className="btn-outline flex-1"
                            >
                                取消
                            </button>
                            <button
                                className="btn-primary flex-1"
                                onClick={handleCreate}
                                disabled={!newCiData.name || !newCiData.typeCode || !newCiData.identifier}
                            >
                                创建配置项
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
