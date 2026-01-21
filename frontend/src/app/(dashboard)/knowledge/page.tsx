'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    BookOpen,
    FileText,
    FolderPlus,
    MoreVertical,
    Plus,
    Search,
    Settings,
    Loader2,
    AlertCircle,
} from 'lucide-react';
import {
    getKnowledgeBases,
    createKnowledgeBase,
    type KnowledgeBase,
} from '@/lib/api';

// 格式化日期
function formatDate(dateString: string): string {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN');
    } catch {
        return dateString;
    }
}

export default function KnowledgePage() {
    // 知识库列表状态
    const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 模态框和表单状态
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [newKbName, setNewKbName] = useState('');
    const [newKbDescription, setNewKbDescription] = useState('');
    const [isCreating, setIsCreating] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);

    // 加载知识库列表
    useEffect(() => {
        loadKnowledgeBases();
    }, []);

    const loadKnowledgeBases = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await getKnowledgeBases(1, 100);
            setKnowledgeBases(response.items);
        } catch (err) {
            console.error('Failed to load knowledge bases:', err);
            setError(err instanceof Error ? err.message : '加载知识库列表失败');
        } finally {
            setLoading(false);
        }
    };

    // 过滤知识库
    const filteredKBs = knowledgeBases.filter(
        (kb) =>
            kb.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (kb.description || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

    // 创建知识库
    const handleCreateKnowledgeBase = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!newKbName.trim()) {
            setCreateError('请输入知识库名称');
            return;
        }

        setIsCreating(true);
        setCreateError(null);

        try {
            const newKb = await createKnowledgeBase({
                name: newKbName.trim(),
                description: newKbDescription.trim() || undefined,
            });

            // 添加到列表
            setKnowledgeBases(prev => [newKb, ...prev]);

            // 重置表单并关闭模态框
            setNewKbName('');
            setNewKbDescription('');
            setShowCreateModal(false);
        } catch (err) {
            console.error('Failed to create knowledge base:', err);
            setCreateError(err instanceof Error ? err.message : '创建失败');
        } finally {
            setIsCreating(false);
        }
    };

    // 关闭模态框
    const handleCloseModal = () => {
        setShowCreateModal(false);
        setNewKbName('');
        setNewKbDescription('');
        setCreateError(null);
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 页面标题 */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">知识库</h1>
                    <p className="text-muted-foreground mt-1">管理和检索企业知识文档</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus className="h-4 w-4" />
                    新建知识库
                </button>
            </div>

            {/* 快捷入口 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Link
                    href="/knowledge/qa"
                    className="card p-4 flex items-center gap-4 hover:border-primary/50 transition-colors cursor-pointer"
                >
                    <div className="p-3 rounded-lg bg-primary/10 text-primary">
                        <BookOpen className="h-6 w-6" />
                    </div>
                    <div>
                        <h3 className="font-medium text-foreground">智能问答</h3>
                        <p className="text-sm text-muted-foreground">基于知识库的AI问答</p>
                    </div>
                </Link>
                <Link
                    href="/knowledge/search"
                    className="card p-4 flex items-center gap-4 hover:border-primary/50 transition-colors cursor-pointer"
                >
                    <div className="p-3 rounded-lg bg-accent/10 text-accent">
                        <Search className="h-6 w-6" />
                    </div>
                    <div>
                        <h3 className="font-medium text-foreground">全文检索</h3>
                        <p className="text-sm text-muted-foreground">跨知识库语义搜索</p>
                    </div>
                </Link>
                <div className="card p-4 flex items-center gap-4 hover:border-primary/50 transition-colors cursor-pointer">
                    <div className="p-3 rounded-lg bg-success/10 text-success">
                        <FileText className="h-6 w-6" />
                    </div>
                    <div>
                        <h3 className="font-medium text-foreground">文档总数</h3>
                        <p className="text-sm text-muted-foreground">
                            {knowledgeBases.reduce((acc, kb) => acc + kb.document_count, 0)} 篇文档
                        </p>
                    </div>
                </div>
            </div>

            {/* 搜索栏 */}
            <div className="card p-4">
                <div className="flex items-center gap-4">
                    <div className="relative max-w-md flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="搜索知识库..."
                            className="input pl-10 w-full"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <button
                        onClick={loadKnowledgeBases}
                        className="btn-outline"
                        disabled={loading}
                    >
                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : '刷新'}
                    </button>
                </div>
            </div>

            {/* 错误提示 */}
            {error && (
                <div className="card p-4 bg-error/10 border-error/50 flex items-center gap-3">
                    <AlertCircle className="h-5 w-5 text-error" />
                    <span className="text-error">{error}</span>
                    <button onClick={loadKnowledgeBases} className="ml-auto btn-outline text-sm">
                        重试
                    </button>
                </div>
            )}

            {/* 加载状态 */}
            {loading && (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <span className="ml-3 text-muted-foreground">加载中...</span>
                </div>
            )}

            {/* 知识库列表 */}
            {!loading && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredKBs.map((kb) => (
                        <div
                            key={kb.id}
                            className="card p-6 hover:border-primary/50 transition-colors group"
                        >
                            <div className="flex items-start justify-between">
                                <div className="p-3 rounded-lg bg-primary/10 text-primary">
                                    <FolderPlus className="h-6 w-6" />
                                </div>
                                <div className="relative">
                                    <button className="p-1.5 rounded-md text-muted-foreground hover:bg-accent/10 hover:text-accent opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
                                        <MoreVertical className="h-5 w-5" />
                                    </button>
                                </div>
                            </div>

                            <Link href={`/knowledge/${kb.id}`} className="block mt-4">
                                <h3 className="font-semibold text-foreground hover:text-primary transition-colors cursor-pointer">
                                    {kb.name}
                                </h3>
                                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                    {kb.description || '暂无描述'}
                                </p>
                            </Link>

                            <div className="mt-4 pt-4 border-t border-border flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">
                                    {kb.document_count} 篇文档
                                </span>
                                <span className="text-muted-foreground">
                                    更新于 {formatDate(kb.updated_at)}
                                </span>
                            </div>

                            <div className="mt-3 flex gap-2">
                                <Link
                                    href={`/knowledge/${kb.id}`}
                                    className="btn-outline text-sm flex-1 justify-center"
                                >
                                    查看文档
                                </Link>
                                <Link
                                    href={`/knowledge/${kb.id}/settings`}
                                    className="btn-ghost p-2"
                                >
                                    <Settings className="h-4 w-4" />
                                </Link>
                            </div>
                        </div>
                    ))}

                    {/* 新建知识库卡片 */}
                    <div
                        onClick={() => setShowCreateModal(true)}
                        className="card p-6 border-dashed flex flex-col items-center justify-center min-h-[200px] hover:border-primary/50 transition-colors cursor-pointer"
                    >
                        <div className="p-4 rounded-full bg-muted text-muted-foreground">
                            <Plus className="h-8 w-8" />
                        </div>
                        <span className="mt-3 text-muted-foreground">新建知识库</span>
                    </div>
                </div>
            )}

            {/* 空状态 */}
            {!loading && !error && filteredKBs.length === 0 && knowledgeBases.length === 0 && (
                <div className="card p-12 text-center">
                    <FolderPlus className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-2">还没有知识库</h3>
                    <p className="text-muted-foreground mb-4">创建您的第一个知识库，开始管理文档</p>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="btn-primary"
                    >
                        <Plus className="h-4 w-4 mr-2" />
                        新建知识库
                    </button>
                </div>
            )}

            {/* 创建知识库模态框 */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-md animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-4">新建知识库</h2>

                        {createError && (
                            <div className="mb-4 p-3 bg-error/10 border border-error/50 rounded-lg text-error text-sm">
                                {createError}
                            </div>
                        )}

                        <form onSubmit={handleCreateKnowledgeBase} className="space-y-4">
                            <div>
                                <label className="label">
                                    知识库名称 <span className="text-error">*</span>
                                </label>
                                <input
                                    type="text"
                                    className="input mt-1 w-full"
                                    placeholder="请输入知识库名称"
                                    value={newKbName}
                                    onChange={(e) => setNewKbName(e.target.value)}
                                    disabled={isCreating}
                                    required
                                />
                            </div>
                            <div>
                                <label className="label">描述</label>
                                <textarea
                                    className="input mt-1 min-h-[100px] w-full resize-none"
                                    placeholder="请输入知识库描述"
                                    value={newKbDescription}
                                    onChange={(e) => setNewKbDescription(e.target.value)}
                                    disabled={isCreating}
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={handleCloseModal}
                                    className="btn-outline flex-1"
                                    disabled={isCreating}
                                >
                                    取消
                                </button>
                                <button
                                    type="submit"
                                    className="btn-primary flex-1 flex items-center justify-center gap-2"
                                    disabled={isCreating || !newKbName.trim()}
                                >
                                    {isCreating && <Loader2 className="h-4 w-4 animate-spin" />}
                                    {isCreating ? '创建中...' : '创建'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
