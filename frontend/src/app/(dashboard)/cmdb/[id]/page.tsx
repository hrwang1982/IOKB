'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
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
    Loader2,
    Plus,
    Search,
} from 'lucide-react';
import {
    getCI,
    updateCI,
    deleteCI,
    getCIType,
    getCIs,
    getCIRelationships,
    createCIRelationship,
    deleteCIRelationship,
    type CI,
    type CIType,
    type CIRelationship
} from '@/lib/api';
import { DynamicForm } from '@/components/DynamicForm';
import { AlertsTable } from '@/components/monitor/AlertsTable';
import { MetricsChart } from '@/components/monitor/MetricsChart';
import { LogsViewer } from '@/components/monitor/LogsViewer';

const statusConfig = {
    active: { label: '运行中', className: 'bg-success/10 text-success' },
    inactive: { label: '已停用', className: 'bg-muted text-muted-foreground' },
    maintenance: { label: '维护中', className: 'bg-warning/10 text-warning' },
    error: { label: '故障', className: 'bg-error/10 text-error' },
};

export default function CIDetailPage({ params }: { params: { id: string } }) {
    const router = useRouter();
    const [activeTab, setActiveTab] = useState<'attributes' | 'relationships' | 'alerts' | 'metrics' | 'logs'>('attributes');
    const [ci, setCi] = useState<CI | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 编辑相关状态
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [ciType, setCiType] = useState<CIType | null>(null);
    const [editingData, setEditingData] = useState<{
        name: string;
        status: string;
        attributes: Record<string, any>;
    }>({ name: '', status: '', attributes: {} });

    // 关系数据
    const [relationships, setRelationships] = useState<{ upstream: CIRelationship[], downstream: CIRelationship[] }>({ upstream: [], downstream: [] });
    // 加载关系数据
    useEffect(() => {
        if (activeTab === 'relationships' && ci) {
            getCIRelationships(ci.id)
                .then(setRelationships)
                .catch(err => console.error('Load rels failed', err));
        }
    }, [activeTab, ci]);

    const handleDelete = async () => {
        if (!ci || !confirm(`确定要删除配置项 "${ci.name}" 吗？此操作无法撤销。`)) return;
        try {
            await deleteCI(ci.id);
            router.push('/cmdb');
        } catch (error) {
            alert('删除失败: ' + (error as Error).message);
        }
    };

    const handleDeleteRelationship = async (relId: number) => {
        if (!confirm('确定删除此关系吗？')) return;
        try {
            await deleteCIRelationship(relId);
            // 刷新
            if (ci) {
                const rels = await getCIRelationships(ci.id);
                setRelationships(rels);
            }
        } catch (e) {
            alert('删除失败');
        }
    };

    // 添加关系相关状态
    const [isAddRelOpen, setIsAddRelOpen] = useState(false);
    const [relType, setRelType] = useState('depends_on');
    const [targetSearch, setTargetSearch] = useState('');
    const [targetResults, setTargetResults] = useState<CI[]>([]);
    const [selectedTargetId, setSelectedTargetId] = useState<number | null>(null);
    const [isSearching, setIsSearching] = useState(false);

    // 搜索目标配置项
    useEffect(() => {
        if (!isAddRelOpen) return;
        const timer = setTimeout(async () => {
            if (targetSearch.trim()) {
                setIsSearching(true);
                try {
                    const res = await getCIs({ keyword: targetSearch, size: 5 });
                    // 排除自己
                    setTargetResults(res.items.filter(item => item.id !== ci?.id));
                } catch (e) {
                    console.error(e);
                } finally {
                    setIsSearching(false);
                }
            } else {
                setTargetResults([]);
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [targetSearch, isAddRelOpen, ci?.id]);

    const handleAddRelationship = async () => {
        if (!selectedTargetId || !ci) return;
        try {
            await createCIRelationship({
                from_ci_id: ci.id,
                to_ci_id: selectedTargetId,
                rel_type: relType
            });
            setIsAddRelOpen(false);
            setTargetSearch('');
            setSelectedTargetId(null);
            // 刷新列表
            const rels = await getCIRelationships(ci.id);
            setRelationships(rels);
        } catch (e) {
            alert('添加关系失败: ' + (e as Error).message);
        }
    };

    useEffect(() => {
        async function loadCi() {
            try {
                const data = await getCI(parseInt(params.id));
                setCi(data);

                // 加载类型定义以获取Schema
                try {
                    const typeData = await getCIType(data.type_code);
                    setCiType(typeData);
                } catch (e) {
                    console.error('Failed to load CI type schema', e);
                }
            } catch (err) {
                setError((err as Error).message);
            } finally {
                setLoading(false);
            }
        }
        loadCi();
    }, [params.id]);

    // 初始化编辑数据
    useEffect(() => {
        if (ci) {
            setEditingData({
                name: ci.name,
                status: ci.status,
                attributes: ci.attributes || {}
            });
        }
    }, [ci]);

    const handleUpdate = async () => {
        if (!ci) return;
        setIsSaving(true);
        try {
            const updated = await updateCI(ci.id, {
                name: editingData.name,
                status: editingData.status,
                attributes: editingData.attributes
            });
            setCi(updated);
            setIsEditing(false);
        } catch (error) {
            alert('更新失败: ' + (error as Error).message);
        } finally {
            setIsSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error || !ci) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
                <div className="text-error">{error || '配置项不存在'}</div>
                <Link href="/cmdb" className="btn-primary">返回列表</Link>
            </div>
        );
    }

    const status = statusConfig[ci.status as keyof typeof statusConfig] || statusConfig.active;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 面包屑 */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Link href="/cmdb" className="hover:text-primary flex items-center gap-1">
                    <ArrowLeft className="h-4 w-4" />
                    配置项列表
                </Link>
                <ChevronRight className="h-4 w-4" />
                <span className="text-foreground">{ci.name}</span>
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
                                <h1 className="text-xl font-bold text-foreground">{ci.name}</h1>
                                <span
                                    className={`px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                                >
                                    {status.label}
                                </span>
                            </div>
                            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                                <span>类型: {ci.type_name || ci.type_code}</span>
                                <span>标识: {ci.identifier}</span>
                                <span>创建于: {ci.created_at ? new Date(ci.created_at).toLocaleString() : '-'}</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setIsEditing(true)}
                            className="btn-outline flex items-center gap-2"
                        >
                            <Edit className="h-4 w-4" />
                            编辑
                        </button>
                        <button
                            onClick={handleDelete}
                            className="btn-outline text-error hover:bg-error/10 flex items-center gap-2"
                        >
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
                            { key: 'metrics', label: '性能监控' },
                            { key: 'logs', label: '日志' },
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
                        {ciType ? (
                            <DynamicForm
                                schema={ciType.attribute_schema}
                                initialValues={ci.attributes}
                                onChange={() => { }} // View mode doesn't change
                                mode="view"
                            />
                        ) : (
                            <div className="text-center text-muted-foreground">加载配置项类型定义中...</div>
                        )}
                        {(!ci.attributes || Object.keys(ci.attributes).length === 0) && !ciType && (
                            <div className="col-span-2 text-center text-muted-foreground py-8">
                                暂无属性信息
                            </div>
                        )}
                    </div>
                )}

                {/* 关系拓扑 */}
                {activeTab === 'relationships' && (
                    <div className="p-6 space-y-6">
                        <div className="flex justify-between items-center">
                            <h3 className="text-lg font-medium">配置项关系</h3>
                            <button
                                onClick={() => setIsAddRelOpen(true)}
                                className="btn-primary btn-sm flex items-center gap-2"
                            >
                                <Plus className="h-4 w-4" />
                                添加关系
                            </button>
                        </div>

                        {/* 上游依赖 */}
                        <div>
                            <h3 className="text-sm font-medium text-muted-foreground mb-3">
                                上游依赖 (被依赖) - {relationships.upstream.length}
                            </h3>
                            <div className="space-y-2">
                                {relationships.upstream.length > 0 ? relationships.upstream.map((rel) => (
                                    <div
                                        key={rel.id}
                                        className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-primary/50 transition-colors"
                                    >
                                        <Network className="h-5 w-5 text-primary" />
                                        <div className="flex-1">
                                            <Link href={`/cmdb/${rel.from_ci_id}`} className="font-medium text-foreground hover:underline">
                                                {rel.from_ci_name}
                                            </Link>
                                            <div className="text-sm text-muted-foreground">ID: {rel.from_ci_id}</div>
                                        </div>
                                        <div className="text-xs px-2 py-1 bg-muted rounded">
                                            {rel.rel_type}
                                        </div>
                                        <button
                                            onClick={() => handleDeleteRelationship(rel.id)}
                                            className="text-muted-foreground hover:text-error p-1"
                                            title="删除关系"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                )) : (
                                    <div className="text-sm text-muted-foreground italic pl-2">无上游依赖</div>
                                )}
                            </div>
                        </div>

                        {/* 下游依赖 */}
                        <div>
                            <h3 className="text-sm font-medium text-muted-foreground mb-3">
                                下游依赖 (依赖于) - {relationships.downstream.length}
                            </h3>
                            <div className="space-y-2">
                                {relationships.downstream.length > 0 ? relationships.downstream.map((rel) => (
                                    <div
                                        key={rel.id}
                                        className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-primary/50 transition-colors"
                                    >
                                        <Database className="h-5 w-5 text-accent" />
                                        <div className="flex-1">
                                            <Link href={`/cmdb/${rel.to_ci_id}`} className="font-medium text-foreground hover:underline">
                                                {rel.to_ci_name}
                                            </Link>
                                            <div className="text-sm text-muted-foreground">ID: {rel.to_ci_id}</div>
                                        </div>
                                        <div className="text-xs px-2 py-1 bg-muted rounded">
                                            {rel.rel_type}
                                        </div>
                                        <button
                                            onClick={() => handleDeleteRelationship(rel.id)}
                                            className="text-muted-foreground hover:text-error p-1"
                                            title="删除关系"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                )) : (
                                    <div className="text-sm text-muted-foreground italic pl-2">无下游依赖</div>
                                )}
                            </div>
                        </div>

                        <div className="pt-4 border-t border-border">
                            <Link
                                href={`/cmdb/topology?ci_id=${ci?.id}`}
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
                        <AlertsTable ciIdentifier={ci.identifier} />
                    </div>
                )}

                {/* 性能监控 */}
                {activeTab === 'metrics' && (
                    <div className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <MetricsChart
                                ciIdentifier={ci.identifier}
                                metricName="cpu_usage"
                                title="CPU 使用率"
                                unit="%"
                                color="#ef4444"
                            />
                            <MetricsChart
                                ciIdentifier={ci.identifier}
                                metricName="memory_usage"
                                title="内存使用率"
                                unit="%"
                                color="#8b5cf6"
                            />
                            <MetricsChart
                                ciIdentifier={ci.identifier}
                                metricName="disk_io_read"
                                title="磁盘 IO (Read)"
                                unit="IOPS"
                                color="#10b981"
                            />
                            <MetricsChart
                                ciIdentifier={ci.identifier}
                                metricName="disk_io_write"
                                title="磁盘 IO (Write)"
                                unit="IOPS"
                                color="#f59e0b"
                            />
                        </div>
                    </div>
                )}

                {/* 日志 */}
                {activeTab === 'logs' && (
                    <div className="p-6">
                        <LogsViewer ciIdentifier={ci.identifier} />
                    </div>
                )}
            </div>

            {/* 编辑模态框 */}
            {isEditing && ci && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="card p-6 w-full max-w-lg animate-slide-in max-h-[90vh] overflow-y-auto">
                        <h2 className="text-lg font-semibold text-foreground mb-4">编辑配置项</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    配置项名称
                                </label>
                                <input
                                    type="text"
                                    className="input w-full"
                                    value={editingData.name || ''}
                                    onChange={(e) => setEditingData({ ...editingData, name: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    状态
                                </label>
                                <select
                                    className="input w-full"
                                    value={editingData.status || ''}
                                    onChange={(e) => setEditingData({ ...editingData, status: e.target.value })}
                                >
                                    <option value="active">运行中</option>
                                    <option value="inactive">已停用</option>
                                    <option value="maintenance">维护中</option>
                                    <option value="error">故障</option>
                                </select>
                            </div>

                            <div className="border-t border-border pt-4 mt-2">
                                <h3 className="text-sm font-medium mb-3">属性信息</h3>
                                <DynamicForm
                                    schema={ciType?.attribute_schema}
                                    initialValues={editingData.attributes}
                                    onChange={(values) => setEditingData(prev => ({ ...prev, attributes: values }))}
                                    mode="edit"
                                />
                            </div>
                        </div>
                        <div className="flex gap-3 pt-6">
                            <button
                                onClick={() => setIsEditing(false)}
                                className="btn-outline flex-1"
                                disabled={isSaving}
                            >
                                取消
                            </button>
                            <button
                                className="btn-primary flex-1"
                                onClick={handleUpdate}
                                disabled={isSaving}
                            >
                                {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                                保存修改
                            </button>
                        </div>
                    </div>
                </div>
            )}
            {/* 添加关系模态框 */}
            {isAddRelOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-md animate-slide-in">
                        <h2 className="text-lg font-semibold mb-4">添加关联关系</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">关系类型</label>
                                <select
                                    className="input w-full"
                                    value={relType}
                                    onChange={(e) => setRelType(e.target.value)}
                                >
                                    <option value="depends_on">依赖于 (Depends On)</option>
                                    <option value="contains">包含 (Contains)</option>
                                    <option value="connects_to">连接到 (Connects To)</option>
                                    <option value="runs_on">运行在 (Runs On)</option>
                                    <option value="deployed_on">部署在 (Deployed On)</option>
                                    <option value="belongs_to">属于 (Belongs To)</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">目标配置项</label>
                                <div className="relative">
                                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                    <input
                                        className="input w-full pl-9"
                                        placeholder="搜索配置项名称/标识..."
                                        value={targetSearch}
                                        onChange={(e) => setTargetSearch(e.target.value)}
                                    />
                                </div>

                                {/* 搜索结果 */}
                                <div className="mt-2 border border-border rounded-md max-h-40 overflow-y-auto">
                                    {isSearching ? (
                                        <div className="p-2 text-center text-sm text-muted-foreground">搜索中...</div>
                                    ) : targetResults.length > 0 ? (
                                        targetResults.map(item => (
                                            <div
                                                key={item.id}
                                                className={`p-2 text-sm cursor-pointer hover:bg-accent/10 flex justify-between items-center ${selectedTargetId === item.id ? 'bg-primary/10 text-primary' : ''}`}
                                                onClick={() => setSelectedTargetId(item.id)}
                                            >
                                                <span>{item.name}</span>
                                                <span className="text-xs text-muted-foreground">{item.identifier}</span>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="p-2 text-center text-sm text-muted-foreground">
                                            {targetSearch ? '未找到相关配置项' : '请输入关键词搜索'}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-3 pt-6">
                            <button
                                onClick={() => setIsAddRelOpen(false)}
                                className="btn-outline flex-1"
                            >
                                取消
                            </button>
                            <button
                                className="btn-primary flex-1"
                                onClick={handleAddRelationship}
                                disabled={!selectedTargetId}
                            >
                                确认添加
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
