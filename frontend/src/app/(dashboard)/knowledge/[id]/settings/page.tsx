'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
    ArrowLeft,
    ChevronRight,
    Loader2,
    Save,
    Trash2,
    AlertCircle,
} from 'lucide-react';
import {
    getKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase,
    type KnowledgeBase,
} from '@/lib/api';

export default function KnowledgeSettingsPage() {
    const params = useParams();
    const router = useRouter();
    const kbId = params.id as string;

    const [kbDetail, setKbDetail] = useState<KnowledgeBase | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    // 表单状态
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');

    // 删除确认状态
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    // 加载知识库详情
    useEffect(() => {
        if (kbId) {
            loadData();
        }
    }, [kbId]);

    const loadData = async () => {
        try {
            setLoading(true);
            setError(null);
            const kb = await getKnowledgeBase(parseInt(kbId));
            setKbDetail(kb);
            setName(kb.name);
            setDescription(kb.description || '');
        } catch (err) {
            console.error('Failed to load knowledge base:', err);
            setError(err instanceof Error ? err.message : '加载失败');
        } finally {
            setLoading(false);
        }
    };

    // 保存设置
    const handleSave = async () => {
        if (!name.trim()) {
            setError('知识库名称不能为空');
            return;
        }

        setSaving(true);
        setError(null);
        setSuccessMessage(null);

        try {
            await updateKnowledgeBase(parseInt(kbId), {
                name: name.trim(),
                description: description.trim() || undefined,
            });

            setSuccessMessage('设置已保存');
            setTimeout(() => setSuccessMessage(null), 3000);

            // 重新加载数据
            await loadData();
        } catch (err) {
            console.error('Failed to save settings:', err);
            setError(err instanceof Error ? err.message : '保存失败');
        } finally {
            setSaving(false);
        }
    };

    // 删除知识库
    const handleDelete = async () => {
        setIsDeleting(true);
        try {
            await deleteKnowledgeBase(parseInt(kbId));
            // 删除成功后返回知识库列表
            router.push('/knowledge');
        } catch (err) {
            console.error('Failed to delete knowledge base:', err);
            setError(err instanceof Error ? err.message : '删除失败');
            setIsDeleting(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <span className="ml-3 text-muted-foreground">加载中...</span>
            </div>
        );
    }

    if (!kbDetail) {
        return (
            <div className="card p-6 text-center">
                <AlertCircle className="h-12 w-12 mx-auto text-error mb-4" />
                <p className="text-error mb-4">知识库不存在</p>
                <Link href="/knowledge" className="btn-primary">
                    返回知识库列表
                </Link>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 面包屑 */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Link href="/knowledge" className="hover:text-primary flex items-center gap-1">
                    <ArrowLeft className="h-4 w-4" />
                    知识库
                </Link>
                <ChevronRight className="h-4 w-4" />
                <Link href={`/knowledge/${kbId}`} className="hover:text-primary">
                    {kbDetail.name}
                </Link>
                <ChevronRight className="h-4 w-4" />
                <span className="text-foreground">设置</span>
            </div>

            {/* 页面标题 */}
            <div>
                <h1 className="text-2xl font-bold text-foreground">知识库设置</h1>
                <p className="text-muted-foreground mt-1">管理知识库的基本信息和配置</p>
            </div>

            {/* 成功/错误提示 */}
            {successMessage && (
                <div className="p-4 bg-success/10 border border-success/50 rounded-lg text-success">
                    {successMessage}
                </div>
            )}

            {error && (
                <div className="p-4 bg-error/10 border border-error/50 rounded-lg text-error">
                    {error}
                </div>
            )}

            {/* 基本设置 */}
            <div className="card p-6 space-y-6">
                <div>
                    <h2 className="text-lg font-semibold text-foreground mb-4">基本信息</h2>
                    
                    {/* 知识库名称 */}
                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-foreground">
                            知识库名称 <span className="text-error">*</span>
                        </label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="input w-full"
                            placeholder="请输入知识库名称"
                        />
                    </div>

                    {/* 知识库描述 */}
                    <div className="space-y-2 mt-4">
                        <label className="block text-sm font-medium text-foreground">
                            描述
                        </label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className="input w-full min-h-[100px]"
                            placeholder="请输入知识库描述（可选）"
                        />
                    </div>

                    {/* 保存按钮 */}
                    <div className="flex gap-3 mt-6">
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="btn-primary flex items-center gap-2"
                        >
                            {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                            <Save className="h-4 w-4" />
                            {saving ? '保存中...' : '保存更改'}
                        </button>
                        <Link href={`/knowledge/${kbId}`} className="btn-outline">
                            取消
                        </Link>
                    </div>
                </div>
            </div>

            {/* 危险操作 */}
            <div className="card p-6 border-error/20">
                <h2 className="text-lg font-semibold text-error mb-4">危险操作</h2>
                <div className="space-y-4">
                    <div>
                        <p className="text-sm text-muted-foreground mb-3">
                            删除知识库将永久删除所有相关的文档和数据，此操作不可撤销。
                        </p>
                        <button
                            onClick={() => setShowDeleteConfirm(true)}
                            className="bg-error hover:bg-error/90 text-white px-4 py-2 rounded-lg flex items-center gap-2"
                        >
                            <Trash2 className="h-4 w-4" />
                            删除知识库
                        </button>
                    </div>
                </div>
            </div>

            {/* 删除确认对话框 */}
            {showDeleteConfirm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-md animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-4">确认删除</h2>
                        <p className="text-muted-foreground mb-6">
                            确定要删除知识库{' '}
                            <span className="font-medium text-foreground">{kbDetail.name}</span>{' '}
                            吗？此操作将永久删除该知识库及其所有文档数据，不可恢复。
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowDeleteConfirm(false)}
                                className="btn-outline flex-1"
                                disabled={isDeleting}
                            >
                                取消
                            </button>
                            <button
                                onClick={handleDelete}
                                className="bg-error hover:bg-error/90 text-white px-4 py-2 rounded-lg flex-1 flex items-center justify-center gap-2"
                                disabled={isDeleting}
                            >
                                {isDeleting && <Loader2 className="h-4 w-4 animate-spin" />}
                                {isDeleting ? '删除中...' : '确认删除'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
