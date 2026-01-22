'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
    ArrowLeft,
    ChevronRight,
    Download,
    Eye,
    File,
    FileImage,
    FileText,
    FileSpreadsheet,
    Filter,
    Loader2,
    MoreVertical,
    Plus,
    RefreshCw,
    Search,
    Settings,
    Trash2,
    Upload,
    X,
    AlertCircle,
} from 'lucide-react';
import {
    getKnowledgeBase,
    getDocuments,
    uploadDocuments,
    deleteDocument,
    reprocessDocument,
    getDocumentDownloadUrl,
    type KnowledgeBase,
    type Document,
} from '@/lib/api';

const fileIcons: Record<string, typeof File> = {
    pdf: File,
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

export default function KnowledgeDetailPage() {
    const params = useParams();
    const kbId = params.id as string;

    // 知识库和文档状态
    const [kbDetail, setKbDetail] = useState<KnowledgeBase | null>(null);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 搜索和模态框状态
    const [searchQuery, setSearchQuery] = useState('');
    const [showUploadModal, setShowUploadModal] = useState(false);

    // 上传状态
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // 删除确认对话框状态
    const [deleteConfirm, setDeleteConfirm] = useState<{ show: boolean; docId: number | null; filename: string }>({
        show: false,
        docId: null,
        filename: '',
    });
    const [isDeleting, setIsDeleting] = useState(false);
    const [isReprocessing, setIsReprocessing] = useState<number | null>(null);

    // 加载知识库详情和文档列表
    useEffect(() => {
        if (kbId) {
            loadData();
        }
    }, [kbId]);

    const loadData = async () => {
        try {
            setLoading(true);
            setError(null);

            const [kb, docs] = await Promise.all([
                getKnowledgeBase(parseInt(kbId)),
                getDocuments(parseInt(kbId)),
            ]);

            setKbDetail(kb);
            setDocuments(docs.items);
        } catch (err) {
            console.error('Failed to load data:', err);
            setError(err instanceof Error ? err.message : '加载失败');
        } finally {
            setLoading(false);
        }
    };

    // 过滤文档
    const filteredDocs = documents.filter((doc) =>
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // 处理文件选择
    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const newFiles = Array.from(e.target.files);
            setSelectedFiles(prev => [...prev, ...newFiles]);
        }
    };

    // 移除选中的文件
    const removeFile = (index: number) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    };

    // 处理文件上传
    const handleUpload = async () => {
        if (selectedFiles.length === 0) {
            setUploadError('请先选择要上传的文件');
            return;
        }

        setIsUploading(true);
        setUploadError(null);

        try {
            // 创建 FileList 模拟对象
            const dataTransfer = new DataTransfer();
            selectedFiles.forEach(file => dataTransfer.items.add(file));

            await uploadDocuments(parseInt(kbId), dataTransfer.files);

            // 上传成功，重新加载文档列表
            await loadData();

            // 关闭模态框，清空选中文件
            setShowUploadModal(false);
            setSelectedFiles([]);
        } catch (err) {
            console.error('Upload failed:', err);
            setUploadError(err instanceof Error ? err.message : '上传失败');
        } finally {
            setIsUploading(false);
        }
    };

    // 关闭上传模态框
    const handleCloseModal = () => {
        setShowUploadModal(false);
        setSelectedFiles([]);
        setUploadError(null);
    };

    // 处理拖放
    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        if (e.dataTransfer.files) {
            const newFiles = Array.from(e.dataTransfer.files);
            setSelectedFiles(prev => [...prev, ...newFiles]);
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
    };

    // 查看文档详情
    const handleViewDocument = (docId: number) => {
        window.location.href = `/knowledge/${kbId}/doc/${docId}`;
    };

    // 下载文档
    const handleDownloadDocument = (docId: number) => {
        const url = getDocumentDownloadUrl(parseInt(kbId), docId);
        // 创建临时链接触发下载
        const link = window.document.createElement('a');
        link.href = url;
        link.download = ''; // 使用服务器返回的文件名
        window.document.body.appendChild(link);
        link.click();
        window.document.body.removeChild(link);
    };

    // 重新处理文档
    const handleReprocessDocument = async (docId: number) => {
        if (isReprocessing === docId) return;

        setIsReprocessing(docId);
        try {
            await reprocessDocument(parseInt(kbId), docId);
            await loadData();
        } catch (err) {
            console.error('Reprocess failed:', err);
            alert(err instanceof Error ? err.message : '重新处理失败');
        } finally {
            setIsReprocessing(null);
        }
    };

    // 显示删除确认对话框
    const showDeleteConfirm = (docId: number, filename: string) => {
        setDeleteConfirm({ show: true, docId, filename });
    };

    // 确认删除
    const handleDeleteDocument = async () => {
        if (!deleteConfirm.docId) return;

        setIsDeleting(true);
        try {
            await deleteDocument(parseInt(kbId), deleteConfirm.docId);
            await loadData();
            setDeleteConfirm({ show: false, docId: null, filename: '' });
        } catch (err) {
            console.error('Delete failed:', err);
            alert(err instanceof Error ? err.message : '删除失败');
        } finally {
            setIsDeleting(false);
        }
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

    if (!kbDetail) {
        return (
            <div className="card p-6 text-center">
                <p className="text-muted-foreground">知识库不存在</p>
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
                <span className="text-foreground">{kbDetail.name}</span>
            </div>

            {/* 知识库信息 */}
            <div className="card p-6">
                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-foreground">{kbDetail.name}</h1>
                        <p className="text-muted-foreground mt-1">{kbDetail.description || '暂无描述'}</p>
                        <div className="flex items-center gap-6 mt-4 text-sm text-muted-foreground">
                            <span>{kbDetail.document_count} 篇文档</span>
                            <span>创建于 {formatDate(kbDetail.created_at).split(' ')[0]}</span>
                            <span>更新于 {formatDate(kbDetail.updated_at)}</span>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Link href={`/knowledge/${kbId}/settings`} className="btn-outline">
                            <Settings className="h-4 w-4 mr-2" />
                            设置
                        </Link>
                        <button
                            onClick={() => setShowUploadModal(true)}
                            className="btn-primary"
                        >
                            <Upload className="h-4 w-4 mr-2" />
                            上传文档
                        </button>
                    </div>
                </div>
            </div>

            {/* 筛选栏 */}
            <div className="card p-4">
                <div className="flex items-center gap-4">
                    <div className="relative flex-1 max-w-sm">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="搜索文档..."
                            className="input pl-10"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <button onClick={loadData} className="btn-outline">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        刷新
                    </button>
                </div>
            </div>

            {/* 文档列表 */}
            <div className="card overflow-hidden">
                <table className="w-full">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                文档名称
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                类型
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                大小
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                状态
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                切片数
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                上传时间
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                操作
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {filteredDocs.map((doc) => {
                            const FileIcon = fileIcons[doc.file_type] || File;
                            const status = statusConfig[doc.status as keyof typeof statusConfig] || statusConfig.pending;

                            return (
                                <tr
                                    key={doc.id}
                                    className="hover:bg-accent/5 transition-colors"
                                >
                                    <td className="px-4 py-4">
                                        <div className="flex items-center gap-3">
                                            <FileIcon className="h-5 w-5 text-primary shrink-0" />
                                            <Link
                                                href={`/knowledge/${kbId}/doc/${doc.id}`}
                                                className="font-medium text-foreground hover:text-primary cursor-pointer"
                                            >
                                                {doc.filename}
                                            </Link>
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground uppercase">
                                        {doc.file_type}
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground">
                                        {formatFileSize(doc.file_size)}
                                    </td>
                                    <td className="px-4 py-4">
                                        <span
                                            className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                                        >
                                            {status.label}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground">
                                        {doc.chunk_count}
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground">
                                        {formatDate(doc.created_at)}
                                    </td>
                                    <td className="px-4 py-4">
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => handleViewDocument(doc.id)}
                                                className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded cursor-pointer"
                                                title="查看详情"
                                            >
                                                <Eye className="h-4 w-4" />
                                            </button>
                                            <button
                                                onClick={() => handleDownloadDocument(doc.id)}
                                                className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded cursor-pointer"
                                                title="下载文档"
                                            >
                                                <Download className="h-4 w-4" />
                                            </button>
                                            <button
                                                onClick={() => handleReprocessDocument(doc.id)}
                                                disabled={isReprocessing === doc.id}
                                                className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded cursor-pointer disabled:opacity-50"
                                                title="重新处理"
                                            >
                                                <RefreshCw className={`h-4 w-4 ${isReprocessing === doc.id ? 'animate-spin' : ''}`} />
                                            </button>
                                            <button
                                                onClick={() => showDeleteConfirm(doc.id, doc.filename)}
                                                className="p-1.5 text-muted-foreground hover:text-error hover:bg-error/10 rounded cursor-pointer"
                                                title="删除文档"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>

                {filteredDocs.length === 0 && (
                    <div className="p-8 text-center text-muted-foreground">
                        {documents.length === 0 ? '暂无文档，点击上方按钮上传' : '没有找到匹配的文档'}
                    </div>
                )}
            </div>

            {/* 上传模态框 */}
            {showUploadModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-lg animate-slide-in">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-foreground">上传文档</h2>
                            <button
                                onClick={handleCloseModal}
                                className="p-1 text-muted-foreground hover:text-foreground"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>

                        {uploadError && (
                            <div className="mb-4 p-3 bg-error/10 border border-error/50 rounded-lg text-error text-sm">
                                {uploadError}
                            </div>
                        )}

                        {/* 拖放区域 */}
                        <div
                            className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <p className="text-foreground mb-2">拖拽文件到此处上传</p>
                            <p className="text-sm text-muted-foreground mb-4">
                                支持 PDF、Word、Excel、Markdown、图片等格式
                            </p>
                            <button
                                type="button"
                                className="btn-primary"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    fileInputRef.current?.click();
                                }}
                            >
                                选择文件
                            </button>
                            <input
                                ref={fileInputRef}
                                type="file"
                                multiple
                                className="hidden"
                                accept=".pdf,.doc,.docx,.xls,.xlsx,.md,.txt,.png,.jpg,.jpeg"
                                onChange={handleFileSelect}
                            />
                        </div>

                        {/* 已选文件列表 */}
                        {selectedFiles.length > 0 && (
                            <div className="mt-4 space-y-2">
                                <p className="text-sm font-medium text-foreground">
                                    已选择 {selectedFiles.length} 个文件
                                </p>
                                <div className="max-h-40 overflow-y-auto space-y-2">
                                    {selectedFiles.map((file, index) => (
                                        <div
                                            key={index}
                                            className="flex items-center justify-between p-2 bg-muted/50 rounded-lg"
                                        >
                                            <div className="flex items-center gap-2 min-w-0">
                                                <File className="h-4 w-4 text-primary shrink-0" />
                                                <span className="text-sm text-foreground truncate">
                                                    {file.name}
                                                </span>
                                                <span className="text-xs text-muted-foreground shrink-0">
                                                    ({formatFileSize(file.size)})
                                                </span>
                                            </div>
                                            <button
                                                onClick={() => removeFile(index)}
                                                className="p-1 text-muted-foreground hover:text-error shrink-0"
                                            >
                                                <X className="h-4 w-4" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* 按钮 */}
                        <div className="flex gap-3 pt-6">
                            <button
                                onClick={handleCloseModal}
                                className="btn-outline flex-1"
                                disabled={isUploading}
                            >
                                取消
                            </button>
                            <button
                                onClick={handleUpload}
                                className="btn-primary flex-1 flex items-center justify-center gap-2"
                                disabled={isUploading || selectedFiles.length === 0}
                            >
                                {isUploading && <Loader2 className="h-4 w-4 animate-spin" />}
                                {isUploading ? '上传中...' : '开始上传'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 删除确认对话框 */}
            {deleteConfirm.show && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-md animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-4">确认删除</h2>
                        <p className="text-muted-foreground mb-6">
                            确定要删除文档 <span className="font-medium text-foreground">{deleteConfirm.filename}</span> 吗？此操作不可恢复。
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setDeleteConfirm({ show: false, docId: null, filename: '' })}
                                className="btn-outline flex-1"
                                disabled={isDeleting}
                            >
                                取消
                            </button>
                            <button
                                onClick={handleDeleteDocument}
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
