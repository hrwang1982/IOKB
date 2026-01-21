'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Bell, Search, User, FileText, Database, AlertTriangle, X } from 'lucide-react';
import { ThemeToggle } from '@/components/theme-toggle';

// 模拟搜索数据
const mockSearchData = {
    knowledge: [
        { id: 1, title: 'CPU使用率过高处理方案.pdf', type: 'document', path: '/knowledge/1/doc/1' },
        { id: 2, title: 'Linux服务器性能优化指南.docx', type: 'document', path: '/knowledge/1/doc/2' },
        { id: 3, title: '运维知识库', type: 'kb', path: '/knowledge/1' },
    ],
    cmdb: [
        { id: 1, name: 'server-prod-001', type: '物理服务器', path: '/cmdb/1' },
        { id: 2, name: 'db-master-001', type: '数据库', path: '/cmdb/2' },
        { id: 3, name: 'router-core-001', type: '网络设备', path: '/cmdb/3' },
    ],
    alerts: [
        { id: 'ALT-2026-001', title: 'CPU使用率超过90%', level: 'critical', path: '/alerts/ALT-2026-001' },
        { id: 'ALT-2026-002', title: '内存使用率告警', level: 'warning', path: '/alerts/ALT-2026-002' },
    ],
};

interface SearchResult {
    category: string;
    items: { id: string | number; title: string; subtitle?: string; path: string; icon: typeof FileText }[];
}

export function Header() {
    const [searchQuery, setSearchQuery] = useState('');
    const [showResults, setShowResults] = useState(false);
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const searchRef = useRef<HTMLDivElement>(null);
    const router = useRouter();

    // 搜索逻辑
    useEffect(() => {
        if (!searchQuery.trim()) {
            setSearchResults([]);
            return;
        }

        const query = searchQuery.toLowerCase();
        const results: SearchResult[] = [];

        // 搜索知识库
        const kbResults = mockSearchData.knowledge.filter(
            item => item.title.toLowerCase().includes(query)
        );
        if (kbResults.length > 0) {
            results.push({
                category: '知识库',
                items: kbResults.map(item => ({
                    id: item.id,
                    title: item.title,
                    subtitle: item.type === 'kb' ? '知识库' : '文档',
                    path: item.path,
                    icon: FileText,
                })),
            });
        }

        // 搜索CMDB
        const cmdbResults = mockSearchData.cmdb.filter(
            item => item.name.toLowerCase().includes(query) || item.type.toLowerCase().includes(query)
        );
        if (cmdbResults.length > 0) {
            results.push({
                category: 'CMDB配置项',
                items: cmdbResults.map(item => ({
                    id: item.id,
                    title: item.name,
                    subtitle: item.type,
                    path: item.path,
                    icon: Database,
                })),
            });
        }

        // 搜索告警
        const alertResults = mockSearchData.alerts.filter(
            item => item.title.toLowerCase().includes(query) || item.id.toLowerCase().includes(query)
        );
        if (alertResults.length > 0) {
            results.push({
                category: '告警',
                items: alertResults.map(item => ({
                    id: item.id,
                    title: item.title,
                    subtitle: item.level === 'critical' ? '紧急' : '警告',
                    path: item.path,
                    icon: AlertTriangle,
                })),
            });
        }

        setSearchResults(results);
    }, [searchQuery]);

    // 点击外部关闭
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setShowResults(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // 处理键盘事件
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Escape') {
            setShowResults(false);
            setSearchQuery('');
        }
    };

    // 导航到结果
    const handleResultClick = (path: string) => {
        router.push(path);
        setShowResults(false);
        setSearchQuery('');
    };

    return (
        <header className="h-16 bg-card border-b border-border flex items-center justify-between px-6">
            {/* 搜索框 */}
            <div className="flex items-center gap-4 flex-1 max-w-xl" ref={searchRef}>
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="搜索知识库、配置项、告警..."
                        className="input pl-10 pr-10 bg-background"
                        value={searchQuery}
                        onChange={(e) => {
                            setSearchQuery(e.target.value);
                            setShowResults(true);
                        }}
                        onFocus={() => setShowResults(true)}
                        onKeyDown={handleKeyDown}
                    />
                    {searchQuery && (
                        <button
                            onClick={() => {
                                setSearchQuery('');
                                setSearchResults([]);
                            }}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground cursor-pointer"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    )}

                    {/* 搜索结果下拉 */}
                    {showResults && searchQuery && (
                        <div className="absolute top-full left-0 right-0 mt-2 bg-card border border-border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
                            {searchResults.length > 0 ? (
                                searchResults.map((group) => (
                                    <div key={group.category}>
                                        <div className="px-3 py-2 text-xs font-semibold text-muted-foreground bg-muted/50">
                                            {group.category}
                                        </div>
                                        {group.items.map((item) => {
                                            const Icon = item.icon;
                                            return (
                                                <button
                                                    key={item.id}
                                                    onClick={() => handleResultClick(item.path)}
                                                    className="w-full px-3 py-2 flex items-center gap-3 hover:bg-accent/10 transition-colors cursor-pointer text-left"
                                                >
                                                    <Icon className="h-4 w-4 text-primary shrink-0" />
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-medium text-foreground truncate">
                                                            {item.title}
                                                        </p>
                                                        {item.subtitle && (
                                                            <p className="text-xs text-muted-foreground">
                                                                {item.subtitle}
                                                            </p>
                                                        )}
                                                    </div>
                                                </button>
                                            );
                                        })}
                                    </div>
                                ))
                            ) : (
                                <div className="px-4 py-8 text-center text-muted-foreground">
                                    未找到匹配的结果
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* 右侧操作 */}
            <div className="flex items-center gap-4">
                <ThemeToggle />

                {/* 通知 */}
                <button className="relative p-2 text-muted-foreground hover:bg-accent/10 hover:text-accent rounded-md transition-colors cursor-pointer">
                    <Bell className="h-5 w-5" />
                    <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full" />
                </button>

                {/* 用户菜单 */}
                <button className="flex items-center gap-2 p-2 text-muted-foreground hover:bg-accent/10 hover:text-accent rounded-md transition-colors cursor-pointer">
                    <div className="w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center">
                        <User className="h-4 w-4 text-primary" />
                    </div>
                    <span className="text-sm font-medium text-foreground">Admin</span>
                </button>
            </div>
        </header>
    );
}
