'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    ArrowLeft,
    ChevronRight,
    FileText,
    Loader2,
    Search,
    Filter,
    AlertCircle,
    Calendar,
    Database,
} from 'lucide-react';
import { getKnowledgeBases, searchKnowledge, KnowledgeBase, SearchResult } from '@/lib/api';

export default function SearchPage() {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [selectedKbId, setSelectedKbId] = useState<string>('all');
    const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
    const [loadingKbs, setLoadingKbs] = useState(true);
    const [results, setResults] = useState<SearchResult[]>([]);
    const [hasSearched, setHasSearched] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 加载知识库列表
    useEffect(() => {
        async function loadKnowledgeBases() {
            try {
                const response = await getKnowledgeBases(1, 100);
                setKnowledgeBases(response.items);
            } catch (error) {
                console.error('Failed to load knowledge bases:', error);
            } finally {
                setLoadingKbs(false);
            }
        }
        loadKnowledgeBases();
    }, []);

    const handleSearch = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!query.trim() || loading) return;

        setLoading(true);
        setError(null);
        setHasSearched(true);
        setResults([]);

        try {
            // 确定要查询的知识库ID
            const kbIds: number[] = selectedKbId === 'all'
                ? knowledgeBases.map(kb => kb.id)
                : [parseInt(selectedKbId)];

            if (kbIds.length === 0) {
                setError('没有可用的知识库');
                setLoading(false);
                return;
            }

            const searchResults = await searchKnowledge(query, kbIds, 20);
            setResults(searchResults);
        } catch (err) {
            console.error('Search failed:', err);
            setError(err instanceof Error ? err.message : '搜索失败');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col animate-fade-in">
            {/* 页面标题 */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Link href="/knowledge" className="hover:text-primary flex items-center gap-1">
                        <ArrowLeft className="h-4 w-4" />
                        知识库
                    </Link>
                    <ChevronRight className="h-4 w-4" />
                    <span className="text-foreground">全文检索</span>
                </div>
            </div>

            {/* 搜索区域 */}
            <div className="py-6 border-b border-border">
                <form onSubmit={handleSearch} className="max-w-4xl mx-auto w-full space-y-4">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="输入关键词搜索文档内容..."
                                className="input pl-10 w-full h-12 text-lg"
                                autoFocus
                            />
                        </div>
                        <div className="w-full md:w-64">
                            <select
                                className="input w-full h-12"
                                value={selectedKbId}
                                onChange={(e) => setSelectedKbId(e.target.value)}
                                disabled={loadingKbs}
                            >
                                <option value="all">所有知识库</option>
                                {knowledgeBases.map((kb) => (
                                    <option key={kb.id} value={kb.id.toString()}>
                                        {kb.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <button
                            type="submit"
                            disabled={loading || !query.trim()}
                            className="btn-primary h-12 px-8 text-lg min-w-[100px]"
                        >
                            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : '搜索'}
                        </button>
                    </div>
                </form>
            </div>

            {/* 结果区域 */}
            <div className="flex-1 overflow-y-auto py-6">
                <div className="max-w-4xl mx-auto space-y-6">
                    {/* 错误提示 */}
                    {error && (
                        <div className="p-4 bg-error/10 border border-error/50 rounded-lg flex items-center gap-3 text-error">
                            <AlertCircle className="h-5 w-5" />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* 搜索结果 */}
                    {results.length > 0 ? (
                        <div className="space-y-4">
                            <p className="text-sm text-muted-foreground mb-4">
                                找到 {results.length} 个相关结果
                            </p>
                            {results.map((result) => (
                                <Link
                                    key={result.chunk_id}
                                    href={`/knowledge/${result.document_id}/doc/${result.document_id}`}
                                    className="block card p-4 hover:border-primary/50 transition-all group"
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <FileText className="h-4 w-4 text-primary" />
                                            <h3 className="font-medium text-foreground group-hover:text-primary transition-colors">
                                                {result.document_name}
                                            </h3>
                                        </div>
                                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                            {/* 相关度 */}
                                            <div className="flex items-center gap-1.5" title="相关度">
                                                <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                                                    <div 
                                                        className="h-full bg-primary transition-all" 
                                                        style={{ width: `${result.score * 100}%` }}
                                                    />
                                                </div>
                                                <span>{(result.score * 100).toFixed(0)}%</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <p className="text-sm text-muted-foreground line-clamp-3 leading-relaxed">
                                        {result.content}
                                    </p>

                                    <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground border-t border-border/50 pt-3">
                                        <div className="flex items-center gap-1">
                                            <Database className="h-3 w-3" />
                                            <span>文档 ID: {result.document_id}</span>
                                        </div>
                                        {/* 这里如果以后API返回了知识库名称，可以显示 */}
                                    </div>
                                </Link>
                            ))}
                        </div>
                    ) : hasSearched && !loading && !error ? (
                        <div className="text-center py-12 text-muted-foreground">
                            <Search className="h-12 w-12 mx-auto mb-4 opacity-20" />
                            <p className="text-lg font-medium text-foreground mb-1">未找到相关内容</p>
                            <p>换个关键词试试看？</p>
                        </div>
                    ) : !hasSearched && (
                        <div className="text-center py-20 text-muted-foreground">
                            <Search className="h-16 w-16 mx-auto mb-6 opacity-10" />
                            <h2 className="text-xl font-medium text-foreground mb-2">知识库全文检索</h2>
                            <p>支持跨多个知识库进行语义搜索，快速找到您需要的内容</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
