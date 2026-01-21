'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
    ArrowLeft,
    ChevronRight,
    Download,
    File,
    FileImage,
    FileText,
    FileSpreadsheet,
    RefreshCw,
    Trash2,
    Eye,
    Copy,
    CheckCircle,
    Loader2,
    AlertCircle,
} from 'lucide-react';
import {
    getKnowledgeBase,
    getDocument,
    reprocessDocument,
    deleteDocument,
    getDocumentDownloadUrl,
    type KnowledgeBase,
    type Document,
} from '@/lib/api';

const fileIcons: Record<string, typeof File> = {
    pdf: FileText,
    docx: FileText,
    doc: FileText,
    md: FileText,
    txt: FileText,
    xlsx: FileSpreadsheet,
    xls: FileSpreadsheet,
    png: FileImage,
    jpg: FileImage,
    jpeg: FileImage,
};

const statusConfig = {
    pending: { label: '待处理', className: 'bg-muted text-muted-foreground' },
    processing: { label: '处理中', className: 'bg-warning/10 text-warning' },
    completed: { label: '已完成', className: 'bg-success/10 text-success' },
    failed: { label: '失败', className: 'bg-error/10 text-error' },
};

function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateString: string): string {
    try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN');
    } catch {
        return dateString;
    }
}

export default function DocumentDetailPage() {
    const params = useParams();
    const kbId = params.id as string;
    const docId = params.docId as string;

    // 状态
    const [kbDetail, setKbDetail] = useState<KnowledgeBase | null>(null);
    const [document, setDocument] = useState<Document | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [activeTab, setActiveTab] = useState<'preview' | 'chunks'>('preview');
    const [copiedChunkId, setCopiedChunkId] = useState<number | null>(null);
    const [isReprocessing, setIsReprocessing] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    // 加载数据
    useEffect(() => {
        if (kbId && docId) {
            loadData();
        }
    }, [kbId, docId]);

    const loadData = async () => {
        try {
            setLoading(true);
            setError(null);

            const [kb, doc] = await Promise.all([
                getKnowledgeBase(parseInt(kbId)),
                getDocument(parseInt(kbId), parseInt(docId)),
            ]);

            setKbDetail(kb);
            setDocument(doc);
        } catch (err) {
            console.error('Failed to load data:', err);
            setError(err instanceof Error ? err.message : '加载失败');
        } finally {
            setLoading(false);
        }
    };

    // 处理函数
    const handleDownload = () => {
        const url = getDocumentDownloadUrl(parseInt(kbId), parseInt(docId));
        window.open(url, '_blank');
    };

    const handleReprocess = async () => {
        if (isReprocessing) return;

        setIsReprocessing(true);
        try {
            await reprocessDocument(parseInt(kbId), parseInt(docId));
            await loadData();
        } catch (err) {
            console.error('Reprocess failed:', err);
            alert(err instanceof Error ? err.message : '重新处理失败');
        } finally {
            setIsReprocessing(false);
        }
    };

    const handleDelete = async () => {
        setIsDeleting(true);
        try {
            await deleteDocument(parseInt(kbId), parseInt(docId));
            // 删除成功后返回知识库详情页
            window.location.href = `/knowledge/${kbId}`;
        } catch (err) {
            console.error('Delete failed:', err);
            alert(err instanceof Error ? err.message : '删除失败');
            setIsDeleting(false);
        }
    };

    const handleCopyChunk = (chunkId: number, content: string) => {
        navigator.clipboard.writeText(content);
        setCopiedChunkId(chunkId);
        setTimeout(() => setCopiedChunkId(null), 2000);
    };

    // 加载中状态
    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <span className="ml-3 text-muted-foreground">加载中...</span>
            </div>
        );
    }

    // 错误状态
    if (error) {
        return (
            <div className="card p-6 text-center">
                <AlertCircle className="h-12 w-12 mx-auto text-error mb-4" />
                <p className="text-error mb-4">{error}</p>
                <button onClick={loadData} className="btn-primary">重试</button>
            </div>
        );
    }

    if (!document || !kbDetail) {
        return (
            <div className="card p-6 text-center">
                <p className="text-muted-foreground">文档不存在</p>
            </div>
        );
    }

    const FileIcon = fileIcons[document.file_type] || File;
    const status = statusConfig[document.status as keyof typeof statusConfig] || statusConfig.pending;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 面包屑导航 */}
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
                <span className="text-foreground">{document.filename}</span>
            </div>

            {/* 文档信息卡片 */}
            <div className="card p-6">
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                        <div className="p-3 rounded-lg bg-primary/10 text-primary">
                            <FileIcon className="h-8 w-8" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-foreground">
                                {document.filename}
                            </h1>
                            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                                <span className="uppercase">{document.file_type}</span>
                                <span>{formatFileSize(document.file_size)}</span>
                                <span>{document.chunk_count} 个切片</span>
                                <span>上传于 {formatDate(document.created_at)}</span>
                            </div>
                            <div className="mt-3">
                                <span
                                    className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                                >
                                    {status.label}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={handleDownload}
                            className="btn-ghost flex items-center gap-2"
                        >
                            <Download className="h-4 w-4" />
                            下载
                        </button>
                        <button
                            onClick={handleReprocess}
                            disabled={isReprocessing}
                            className="btn-ghost flex items-center gap-2"
                        >
                            <RefreshCw className={`h-4 w-4 ${isReprocessing ? 'animate-spin' : ''}`} />
                            {isReprocessing ? '处理中...' : '重新解析'}
                        </button>
                        <button
                            onClick={() => setShowDeleteConfirm(true)}
                            className="btn-ghost text-error flex items-center gap-2"
                        >
                            <Trash2 className="h-4 w-4" />
                            删除
                        </button>
                    </div>
                </div>
            </div>

            {/* 标签页 */}
            <div className="border-b border-border">
                <div className="flex gap-4">
                    <button
                        onClick={() => setActiveTab('preview')}
                        className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${activeTab === 'preview'
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                            }`}
                    >
                        文档信息
                    </button>
                    <button
                        onClick={() => setActiveTab('chunks')}
                        className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${activeTab === 'chunks'
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                            }`}
                    >
                        切片列表 ({document.chunk_count})
                    </button>
                </div>
            </div>

            {/* 内容区域 */}
            {activeTab === 'preview' ? (
                <div className="card p-6">
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <span className="text-sm text-muted-foreground">文件名</span>
                                <p className="font-medium text-foreground">{document.filename}</p>
                            </div>
                            <div>
                                <span className="text-sm text-muted-foreground">文件类型</span>
                                <p className="font-medium text-foreground uppercase">{document.file_type}</p>
                            </div>
                            <div>
                                <span className="text-sm text-muted-foreground">文件大小</span>
                                <p className="font-medium text-foreground">{formatFileSize(document.file_size)}</p>
                            </div>
                            <div>
                                <span className="text-sm text-muted-foreground">处理状态</span>
                                <p className="font-medium">
                                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}>
                                        {status.label}
                                    </span>
                                </p>
                            </div>
                            <div>
                                <span className="text-sm text-muted-foreground">切片数量</span>
                                <p className="font-medium text-foreground">{document.chunk_count}</p>
                            </div>
                            <div>
                                <span className="text-sm text-muted-foreground">上传时间</span>
                                <p className="font-medium text-foreground">{formatDate(document.created_at)}</p>
                            </div>
                        </div>

                        <div className="pt-4 border-t border-border">
                            <p className="text-sm text-muted-foreground mb-2">
                                提示：如需查看文档原始内容，请点击"下载"按钮下载文件。
                            </p>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="space-y-4">
                    {document.chunk_count === 0 ? (
                        <div className="card p-8 text-center text-muted-foreground">
                            暂无切片数据，文档可能正在处理中
                        </div>
                    ) : (
                        <div className="card p-8 text-center text-muted-foreground">
                            切片数据需要后端API支持，暂未实现
                        </div>
                    )}
                </div>
            )}

            {/* 删除确认对话框 */}
            {showDeleteConfirm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-md animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-4">确认删除</h2>
                        <p className="text-muted-foreground mb-6">
                            确定要删除文档 <span className="font-medium text-foreground">{document.filename}</span> 吗？此操作不可恢复。
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
