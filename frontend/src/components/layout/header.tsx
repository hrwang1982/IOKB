'use client';

import { Bell, Search, User } from 'lucide-react';
import { ThemeToggle } from '@/components/theme-toggle';

export function Header() {
    return (
        <header className="h-16 bg-card border-b border-border flex items-center justify-between px-6">
            {/* 搜索框 */}
            <div className="flex items-center gap-4 flex-1 max-w-xl">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="搜索知识库、配置项、告警..."
                        className="input pl-10 bg-background"
                    />
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
