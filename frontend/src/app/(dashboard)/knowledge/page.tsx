'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
    BookOpen,
    FileText,
    FolderPlus,
    MoreVertical,
    Plus,
    Search,
    Settings,
    Trash2,
} from 'lucide-react';

// 模拟知识库数据
const mockKnowledgeBases = [
    {
        id: 1,
        name: '运维知识库',
        description: '包含日常运维操作手册、故障处理方案、最佳实践等文档',
        documentCount: 156,
        status: 'active',
        updatedAt: '2026-01-18 15:30:00',
    },
    {
        id: 2,
        name: '故障处理手册',
        description: '常见故障的处理流程和解决方案汇总',
        documentCount: 89,
        status: 'active',
        updatedAt: '2026-01-17 10:20:00',
    },
    {
        id: 3,
        name: '产品使用文档',
        description: '各类产品的使用指南和配置说明',
        documentCount: 234,
        status: 'active',
        updatedAt: '2026-01-16 18:45:00',
    },
    {
        id: 4,
        name: '安全规范',
        description: '信息安全相关的规范文档和合规要求',
        documentCount: 45,
        status: 'active',
        updatedAt: '2026-01-15 09:00:00',
    },
];

export default function KnowledgePage() {
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    const filteredKBs = mockKnowledgeBases.filter(
        (kb) =>
            kb.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            kb.description.toLowerCase().includes(searchQuery.toLowerCase())
    );

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
                            {mockKnowledgeBases.reduce((acc, kb) => acc + kb.documentCount, 0)} 篇文档
                        </p>
                    </div>
                </div>
            </div>

            {/* 搜索栏 */}
            <div className="card p-4">
                <div className="relative max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="搜索知识库..."
                        className="input pl-10"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {/* 知识库列表 */}
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
                                {kb.description}
                            </p>
                        </Link>

                        <div className="mt-4 pt-4 border-t border-border flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">
                                {kb.documentCount} 篇文档
                            </span>
                            <span className="text-muted-foreground">
                                更新于 {kb.updatedAt.split(' ')[0]}
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

            {/* 创建知识库模态框 */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-md animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-4">新建知识库</h2>
                        <form className="space-y-4">
                            <div>
                                <label className="label">知识库名称</label>
                                <input
                                    type="text"
                                    className="input mt-1"
                                    placeholder="请输入知识库名称"
                                />
                            </div>
                            <div>
                                <label className="label">描述</label>
                                <textarea
                                    className="input mt-1 min-h-[100px]"
                                    placeholder="请输入知识库描述"
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setShowCreateModal(false)}
                                    className="btn-outline flex-1"
                                >
                                    取消
                                </button>
                                <button type="submit" className="btn-primary flex-1">
                                    创建
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
