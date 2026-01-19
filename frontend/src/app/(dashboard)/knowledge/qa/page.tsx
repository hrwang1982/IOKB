'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
    ArrowLeft,
    BookOpen,
    ChevronRight,
    FileText,
    MessageSquare,
    Send,
    Sparkles,
    ThumbsDown,
    ThumbsUp,
    User,
} from 'lucide-react';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: {
        id: number;
        title: string;
        content: string;
        score: number;
    }[];
    timestamp: Date;
}

export default function QAPage() {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content: '您好！我是IOKB智能运维助手，可以帮您解答运维相关问题。请问有什么可以帮助您的？',
            timestamp: new Date(),
        },
    ]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim() || loading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: query,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setQuery('');
        setLoading(true);

        // 模拟AI回答
        await new Promise((r) => setTimeout(r, 2000));

        const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: `关于"${userMessage.content}"，根据知识库的内容，我为您找到了以下信息：

**CPU使用率过高的常见原因：**

1. **应用负载过高** - 突发的业务流量增加导致服务器压力上升
2. **进程异常** - 某个进程出现死循环或内存泄漏
3. **定时任务冲突** - 多个定时任务同时执行
4. **系统更新** - 后台自动更新占用资源

**建议的排查步骤：**

\`\`\`bash
# 查看CPU占用最高的进程
top -c

# 查看特定进程的线程
top -H -p <pid>

# 使用perf分析CPU热点
perf top
\`\`\`

如需更详细的信息，请查看下方引用的文档。`,
            sources: [
                {
                    id: 1,
                    title: 'CPU使用率过高处理方案.pdf',
                    content: '当CPU使用率持续超过80%时，应立即排查...',
                    score: 0.92,
                },
                {
                    id: 2,
                    title: 'Linux服务器性能优化指南.docx',
                    content: 'CPU性能调优包括以下几个方面...',
                    score: 0.85,
                },
            ],
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, aiMessage]);
        setLoading(false);
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
                    <span className="text-foreground">智能问答</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">当前知识库:</span>
                    <select className="input w-48 h-9 text-sm">
                        <option value="all">全部知识库</option>
                        <option value="1">运维知识库</option>
                        <option value="2">故障处理手册</option>
                    </select>
                </div>
            </div>

            {/* 对话区域 */}
            <div className="flex-1 overflow-y-auto py-6 space-y-6">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                        {/* 头像 */}
                        <div
                            className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${message.role === 'user'
                                ? 'bg-primary text-white'
                                : 'bg-accent/20 text-accent'
                                }`}
                        >
                            {message.role === 'user' ? (
                                <User className="h-5 w-5" />
                            ) : (
                                <Sparkles className="h-5 w-5" />
                            )}
                        </div>

                        {/* 消息内容 */}
                        <div
                            className={`max-w-[70%] ${message.role === 'user' ? 'text-right' : ''
                                }`}
                        >
                            <div
                                className={`inline-block p-4 rounded-lg ${message.role === 'user'
                                    ? 'bg-primary text-white'
                                    : 'bg-card border border-border'
                                    }`}
                            >
                                <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
                                    {message.content}
                                </div>
                            </div>

                            {/* 引用来源 */}
                            {message.sources && message.sources.length > 0 && (
                                <div className="mt-3 space-y-2">
                                    <p className="text-xs text-muted-foreground">📚 引用来源:</p>
                                    {message.sources.map((source) => (
                                        <div
                                            key={source.id}
                                            className="p-3 bg-muted/50 rounded-lg border border-border hover:border-primary/50 transition-colors cursor-pointer"
                                        >
                                            <div className="flex items-center gap-2">
                                                <FileText className="h-4 w-4 text-primary shrink-0" />
                                                <span className="text-sm font-medium text-foreground">
                                                    {source.title}
                                                </span>
                                                <span className="ml-auto text-xs text-muted-foreground">
                                                    匹配度 {Math.round(source.score * 100)}%
                                                </span>
                                            </div>
                                            <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
                                                {source.content}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* 反馈按钮 */}
                            {message.role === 'assistant' && message.id !== '1' && (
                                <div className="flex items-center gap-2 mt-2">
                                    <button className="p-1.5 text-muted-foreground hover:text-success hover:bg-success/10 rounded cursor-pointer">
                                        <ThumbsUp className="h-4 w-4" />
                                    </button>
                                    <button className="p-1.5 text-muted-foreground hover:text-error hover:bg-error/10 rounded cursor-pointer">
                                        <ThumbsDown className="h-4 w-4" />
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {/* 加载中 */}
                {loading && (
                    <div className="flex gap-4">
                        <div className="w-10 h-10 rounded-full bg-accent/20 text-accent flex items-center justify-center">
                            <Sparkles className="h-5 w-5" />
                        </div>
                        <div className="p-4 bg-card border border-border rounded-lg">
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                                <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-100" />
                                <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-200" />
                                <span className="text-sm ml-2">正在思考...</span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* 输入区域 */}
            <div className="pt-4 border-t border-border">
                <form onSubmit={handleSubmit} className="flex gap-3">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="输入您的问题，如: 服务器CPU使用率过高怎么处理？"
                        className="input flex-1"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={!query.trim() || loading}
                        className="btn-primary px-6"
                    >
                        <Send className="h-4 w-4" />
                    </button>
                </form>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                    AI回答基于知识库内容生成，仅供参考
                </p>
            </div>
        </div>
    );
}
