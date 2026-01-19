'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
    ArrowLeft,
    CheckCircle,
    ChevronRight,
    File,
    FileImage,
    FilePdf,
    FileSpreadsheet,
    FileText,
    Trash2,
    Upload,
    X,
} from 'lucide-react';

interface UploadFile {
    id: string;
    file: File;
    status: 'pending' | 'uploading' | 'success' | 'error';
    progress: number;
    error?: string;
}

const fileIcons: Record<string, typeof File> = {
    'application/pdf': FilePdf,
    'application/msword': FileText,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileText,
    'text/markdown': FileText,
    'text/plain': FileText,
    'application/vnd.ms-excel': FileSpreadsheet,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': FileSpreadsheet,
    'image/png': FileImage,
    'image/jpeg': FileImage,
};

function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadPage({ params }: { params: { id: string } }) {
    const router = useRouter();
    const [files, setFiles] = useState<UploadFile[]>([]);
    const [dragActive, setDragActive] = useState(false);
    const [uploading, setUploading] = useState(false);

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            addFiles(Array.from(e.dataTransfer.files));
        }
    }, []);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            addFiles(Array.from(e.target.files));
        }
    };

    const addFiles = (newFiles: File[]) => {
        const uploadFiles: UploadFile[] = newFiles.map((file) => ({
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            file,
            status: 'pending',
            progress: 0,
        }));
        setFiles((prev) => [...prev, ...uploadFiles]);
    };

    const removeFile = (id: string) => {
        setFiles((prev) => prev.filter((f) => f.id !== id));
    };

    const handleUpload = async () => {
        if (files.length === 0) return;

        setUploading(true);

        // 模拟上传过程
        for (const uploadFile of files) {
            if (uploadFile.status === 'success') continue;

            setFiles((prev) =>
                prev.map((f) =>
                    f.id === uploadFile.id ? { ...f, status: 'uploading' } : f
                )
            );

            // 模拟进度
            for (let progress = 0; progress <= 100; progress += 20) {
                await new Promise((r) => setTimeout(r, 200));
                setFiles((prev) =>
                    prev.map((f) => (f.id === uploadFile.id ? { ...f, progress } : f))
                );
            }

            setFiles((prev) =>
                prev.map((f) =>
                    f.id === uploadFile.id ? { ...f, status: 'success', progress: 100 } : f
                )
            );
        }

        setUploading(false);
    };

    const allUploaded = files.length > 0 && files.every((f) => f.status === 'success');

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 面包屑 */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Link href="/knowledge" className="hover:text-primary flex items-center gap-1">
                    <ArrowLeft className="h-4 w-4" />
                    知识库
                </Link>
                <ChevronRight className="h-4 w-4" />
                <Link href={`/knowledge/${params.id}`} className="hover:text-primary">
                    运维知识库
                </Link>
                <ChevronRight className="h-4 w-4" />
                <span className="text-foreground">上传文档</span>
            </div>

            {/* 标题 */}
            <div>
                <h1 className="text-2xl font-bold text-foreground">上传文档</h1>
                <p className="text-muted-foreground mt-1">
                    上传文档到知识库，系统将自动解析并建立索引
                </p>
            </div>

            {/* 上传区域 */}
            <div
                className={`card p-8 border-2 border-dashed transition-colors ${dragActive ? 'border-primary bg-primary/5' : 'border-border'
                    }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                <div className="text-center">
                    <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-lg font-medium text-foreground mb-2">
                        拖拽文件到此处上传
                    </p>
                    <p className="text-sm text-muted-foreground mb-4">
                        或点击下方按钮选择文件
                    </p>
                    <label className="btn-primary cursor-pointer inline-flex">
                        选择文件
                        <input
                            type="file"
                            multiple
                            className="hidden"
                            onChange={handleFileSelect}
                            accept=".pdf,.doc,.docx,.xls,.xlsx,.md,.txt,.png,.jpg,.jpeg"
                        />
                    </label>
                    <p className="text-xs text-muted-foreground mt-4">
                        支持格式: PDF、Word、Excel、Markdown、TXT、图片 (单文件最大 50MB)
                    </p>
                </div>
            </div>

            {/* 文件列表 */}
            {files.length > 0 && (
                <div className="card">
                    <div className="p-4 border-b border-border flex items-center justify-between">
                        <h2 className="font-semibold text-foreground">
                            待上传文件 ({files.length})
                        </h2>
                        {!uploading && (
                            <button
                                onClick={() => setFiles([])}
                                className="text-sm text-muted-foreground hover:text-error"
                            >
                                清空列表
                            </button>
                        )}
                    </div>
                    <div className="divide-y divide-border">
                        {files.map((uploadFile) => {
                            const FileIcon = fileIcons[uploadFile.file.type] || File;

                            return (
                                <div
                                    key={uploadFile.id}
                                    className="p-4 flex items-center gap-4"
                                >
                                    <FileIcon className="h-8 w-8 text-primary shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between">
                                            <span className="font-medium text-foreground truncate">
                                                {uploadFile.file.name}
                                            </span>
                                            <span className="text-sm text-muted-foreground ml-4 shrink-0">
                                                {formatFileSize(uploadFile.file.size)}
                                            </span>
                                        </div>
                                        {uploadFile.status === 'uploading' && (
                                            <div className="mt-2">
                                                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-primary rounded-full transition-all"
                                                        style={{ width: `${uploadFile.progress}%` }}
                                                    />
                                                </div>
                                                <span className="text-xs text-muted-foreground mt-1">
                                                    上传中 {uploadFile.progress}%
                                                </span>
                                            </div>
                                        )}
                                        {uploadFile.status === 'success' && (
                                            <div className="flex items-center gap-1 mt-1 text-success text-sm">
                                                <CheckCircle className="h-4 w-4" />
                                                上传成功
                                            </div>
                                        )}
                                    </div>
                                    {uploadFile.status === 'pending' && (
                                        <button
                                            onClick={() => removeFile(uploadFile.id)}
                                            className="p-1.5 text-muted-foreground hover:text-error hover:bg-error/10 rounded cursor-pointer"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* 操作按钮 */}
            <div className="flex justify-end gap-3">
                <Link href={`/knowledge/${params.id}`} className="btn-outline">
                    取消
                </Link>
                {allUploaded ? (
                    <button
                        onClick={() => router.push(`/knowledge/${params.id}`)}
                        className="btn-primary"
                    >
                        完成
                    </button>
                ) : (
                    <button
                        onClick={handleUpload}
                        disabled={files.length === 0 || uploading}
                        className="btn-primary"
                    >
                        {uploading ? '上传中...' : `开始上传 (${files.length})`}
                    </button>
                )}
            </div>
        </div>
    );
}
