'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Bell,
    BookOpen,
    ChevronLeft,
    ChevronRight,
    Database,
    LayoutDashboard,
    Settings,
    Users,
} from 'lucide-react';
import { useState } from 'react';
import { ThemeToggle } from '@/components/theme-toggle';

interface NavItem {
    title: string;
    href: string;
    icon: React.ElementType;
    badge?: number;
}

const mainNav: NavItem[] = [
    { title: '仪表盘', href: '/dashboard', icon: LayoutDashboard },
    { title: '告警中心', href: '/alerts', icon: Bell, badge: 3 },
    { title: '知识库', href: '/knowledge', icon: BookOpen },
    { title: 'CMDB', href: '/cmdb', icon: Database },
];

const adminNav: NavItem[] = [
    { title: '用户管理', href: '/admin/users', icon: Users },
    { title: '系统设置', href: '/settings', icon: Settings },
];

export function Sidebar() {
    const [collapsed, setCollapsed] = useState(false);
    const pathname = usePathname();

    const NavLink = ({ item }: { item: NavItem }) => {
        const isActive = pathname.startsWith(item.href);
        const Icon = item.icon;

        return (
            <Link
                href={item.href}
                className={`
          flex items-center gap-3 px-3 py-2 rounded-md transition-colors cursor-pointer
          ${isActive
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-accent/10 hover:text-accent'
                    }
        `}
            >
                <Icon className="h-5 w-5 shrink-0" />
                {!collapsed && (
                    <>
                        <span className="flex-1">{item.title}</span>
                        {item.badge && (
                            <span className="px-2 py-0.5 text-xs bg-error text-white rounded-full">
                                {item.badge}
                            </span>
                        )}
                    </>
                )}
            </Link>
        );
    };

    return (
        <aside
            className={`
        fixed left-0 top-0 h-screen bg-card border-r border-border
        flex flex-col transition-all duration-300 z-50
        ${collapsed ? 'w-16' : 'w-64'}
      `}
        >
            {/* Logo */}
            <div className="h-16 flex items-center justify-between px-4 border-b border-border">
                {!collapsed && (
                    <span className="text-xl font-bold text-primary">IOKB</span>
                )}
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="p-1.5 rounded-md text-muted-foreground hover:bg-accent/10 hover:text-accent transition-colors cursor-pointer"
                >
                    {collapsed ? (
                        <ChevronRight className="h-5 w-5" />
                    ) : (
                        <ChevronLeft className="h-5 w-5" />
                    )}
                </button>
            </div>

            {/* Main Navigation */}
            <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
                <div className="space-y-1">
                    {mainNav.map((item) => (
                        <NavLink key={item.href} item={item} />
                    ))}
                </div>

                <div className="pt-4 mt-4 border-t border-border space-y-1">
                    {!collapsed && (
                        <span className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                            管理
                        </span>
                    )}
                    {adminNav.map((item) => (
                        <NavLink key={item.href} item={item} />
                    ))}
                </div>
            </nav>

            {/* Footer */}
            <div className="p-3 border-t border-border">
                <div className="flex items-center justify-center">
                    <ThemeToggle />
                </div>
            </div>
        </aside>
    );
}
