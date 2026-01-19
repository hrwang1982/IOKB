'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
    ArrowLeft,
    ChevronRight,
    Download,
    Eye,
    File,
    FileImage,
    FilePdf,
    FileSpreadsheet,
    FileText,
    Filter,
    MoreVertical,
    Plus,
    RefreshCw,
    Search,
    Settings,
    Trash2,
    Upload,
} from 'lucide-react';

// 模拟知识库详情
const kbDetail = {
    id: 1,
    name: '运维知识库',
    description: '包含日常运维操作手册、故障处理方案、最佳实践等文档',
    documentCount: 156,
    status: 'active',
    createdAt: '2026-01-01 10:00:00',
    updatedAt: '2026-01-18 15:30:00',
};

// 模拟文档列表
const mockDocuments = [
    {
        id: 1,
        filename: 'CPU使用率过高处理方案.pdf',
        fileType: 'pdf',
        fileSize: 1024 * 256,
        status: 'completed',
        chunkCount: 12,
        createdAt: '2026-01-18 14:30:00',
    },
    {
        id: 2,
        filename: 'Linux服务器性能优化指南.docx',
        fileType: 'docx',
        fileSize: 1024 * 512,
        status: 'completed',
        chunkCount: 28,
        createdAt: '2026-01-17 10:20:00',
    },
    {
        id: 3,
        filename: '数据库备份恢复手册.md',
        fileType: 'md',
        fileSize: 1024 * 64,
        status: 'completed',
        chunkCount: 8,
        createdAt: '2026-01-16 18:45:00',
    },
    {
        id: 4,
        filename: '网络故障排查流程.xlsx',
        fileType: 'xlsx',
        fileSize: 1024 * 128,
        status: 'processing',
        chunkCount: 0,
        createdAt: '2026-01-18 16:00:00',
    },
    {
        id: 5,
        filename: '服务器配置截图.png',
        fileType: 'png',
        fileSize: 1024 * 1024 * 2,
        status: 'completed',
        chunkCount: 1,
        createdAt: '2026-01-15 09:00:00',
    },
];

const fileIcons: Record<string, typeof File> = {
    pdf: FilePdf,
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

export default function KnowledgeDetailPage({ params }: { params: { id: string } }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [showUploadModal, setShowUploadModal] = useState(false);

    const filteredDocs = mockDocuments.filter((doc) =>
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
    );

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
                        <p className="text-muted-foreground mt-1">{kbDetail.description}</p>
                        <div className="flex items-center gap-6 mt-4 text-sm text-muted-foreground">
                            <span>{kbDetail.documentCount} 篇文档</span>
                            <span>创建于 {kbDetail.createdAt.split(' ')[0]}</span>
                            <span>更新于 {kbDetail.updatedAt}</span>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Link href={`/knowledge/${params.id}/settings`} className="btn-outline">
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
                    <select className="input w-32">
                        <option value="all">全部状态</option>
                        <option value="completed">已完成</option>
                        <option value="processing">处理中</option>
                        <option value="failed">失败</option>
                    </select>
                    <select className="input w-32">
                        <option value="all">全部类型</option>
                        <option value="pdf">PDF</option>
                        <option value="docx">Word</option>
                        <option value="xlsx">Excel</option>
                        <option value="md">Markdown</option>
                    </select>
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
                            const FileIcon = fileIcons[doc.fileType] || File;
                            const status = statusConfig[doc.status as keyof typeof statusConfig];

                            return (
                                <tr
                                    key={doc.id}
                                    className="hover:bg-accent/5 transition-colors"
                                >
                                    <td className="px-4 py-4">
                                        <div className="flex items-center gap-3">
                                            <FileIcon className="h-5 w-5 text-primary shrink-0" />
                                            <Link
                                                href={`/knowledge/${params.id}/doc/${doc.id}`}
                                                className="font-medium text-foreground hover:text-primary cursor-pointer"
                                            >
                                                {doc.filename}
                                            </Link>
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground uppercase">
                                        {doc.fileType}
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground">
                                        {formatFileSize(doc.fileSize)}
                                    </td>
                                    <td className="px-4 py-4">
                                        <span
                                            className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                                        >
                                            {status.label}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground">
                                        {doc.chunkCount}
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground">
                                        {doc.createdAt}
                                    </td>
                                    <td className="px-4 py-4">
                                        <div className="flex items-center gap-2">
                                            <button className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded cursor-pointer">
                                                <Eye className="h-4 w-4" />
                                            </button>
                                            <button className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded cursor-pointer">
                                                <Download className="h-4 w-4" />
                                            </button>
                                            <button className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded cursor-pointer">
                                                <RefreshCw className="h-4 w-4" />
                                            </button>
                                            <button className="p-1.5 text-muted-foreground hover:text-error hover:bg-error/10 rounded cursor-pointer">
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
                        没有找到匹配的文档
                    </div>
                )}
            </div>

            {/* 上传模态框 */}
            {showUploadModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-lg animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-4">上传文档</h2>
                        <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                            <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <p className="text-foreground mb-2">拖拽文件到此处上传</p>
                            <p className="text-sm text-muted-foreground mb-4">
                                支持 PDF、Word、Excel、Markdown、图片等格式
                            </p>
                            <button className="btn-primary">选择文件</button>
                        </div>
                        <div className="flex gap-3 pt-6">
                            <button
                                onClick={() => setShowUploadModal(false)}
                                className="btn-outline flex-1"
                            >
                                取消
                            </button>
                            <button className="btn-primary flex-1">开始上传</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
