'use client';

import { useState } from 'react';
import {
    Edit,
    MoreVertical,
    Plus,
    Search,
    Shield,
    Trash2,
    UserCheck,
    UserPlus,
} from 'lucide-react';

// 模拟用户数据
const mockUsers = [
    {
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        displayName: '系统管理员',
        roles: ['admin'],
        status: 'active',
        lastLogin: '2026-01-18 15:30:00',
        createdAt: '2026-01-01 10:00:00',
    },
    {
        id: 2,
        username: 'operator01',
        email: 'operator01@example.com',
        displayName: '运维工程师01',
        roles: ['kb_admin', 'alert_operator'],
        status: 'active',
        lastLogin: '2026-01-18 14:20:00',
        createdAt: '2026-01-05 09:30:00',
    },
    {
        id: 3,
        username: 'viewer01',
        email: 'viewer01@example.com',
        displayName: '只读用户01',
        roles: ['viewer'],
        status: 'active',
        lastLogin: '2026-01-17 16:45:00',
        createdAt: '2026-01-10 14:20:00',
    },
    {
        id: 4,
        username: 'operator02',
        email: 'operator02@example.com',
        displayName: '运维工程师02',
        roles: ['cmdb_admin'],
        status: 'inactive',
        lastLogin: '2026-01-15 10:00:00',
        createdAt: '2026-01-08 11:15:00',
    },
];

const roleColors: Record<string, string> = {
    admin: 'bg-error/10 text-error',
    kb_admin: 'bg-primary/10 text-primary',
    cmdb_admin: 'bg-accent/10 text-accent',
    alert_operator: 'bg-warning/10 text-warning',
    viewer: 'bg-muted text-muted-foreground',
};

const roleLabels: Record<string, string> = {
    admin: '系统管理员',
    kb_admin: '知识库管理员',
    cmdb_admin: 'CMDB管理员',
    alert_operator: '告警处理员',
    viewer: '只读用户',
};

const statusConfig = {
    active: { label: '启用', className: 'bg-success/10 text-success' },
    inactive: { label: '禁用', className: 'bg-muted text-muted-foreground' },
};

export default function UsersPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [showCreateModal, setShowCreateModal] = useState(false);

    const filteredUsers = mockUsers.filter(
        (user) =>
            user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
            user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
            user.displayName.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 页面标题 */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">用户管理</h1>
                    <p className="text-muted-foreground mt-1">管理系统用户和权限</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <UserPlus className="h-4 w-4" />
                    新建用户
                </button>
            </div>

            {/* 统计概览 */}
            <div className="grid grid-cols-4 gap-4">
                {[
                    { label: '全部用户', value: mockUsers.length, color: 'primary' },
                    {
                        label: '启用中',
                        value: mockUsers.filter((u) => u.status === 'active').length,
                        color: 'success',
                    },
                    {
                        label: '管理员',
                        value: mockUsers.filter((u) => u.roles.includes('admin')).length,
                        color: 'error',
                    },
                    {
                        label: '今日活跃',
                        value: 2,
                        color: 'accent',
                    },
                ].map((stat) => (
                    <div
                        key={stat.label}
                        className="card p-4 cursor-pointer hover:border-primary/50 transition-colors"
                    >
                        <p className="text-sm text-muted-foreground">{stat.label}</p>
                        <p className={`text-2xl font-bold text-${stat.color}`}>{stat.value}</p>
                    </div>
                ))}
            </div>

            {/* 搜索栏 */}
            <div className="card p-4">
                <div className="relative max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="搜索用户名、邮箱或姓名..."
                        className="input pl-10"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {/* 用户列表 */}
            <div className="card overflow-hidden">
                <table className="w-full">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                用户信息
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                角色
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                状态
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                最后登录
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                创建时间
                            </th>
                            <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                                操作
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {filteredUsers.map((user) => {
                            const status = statusConfig[user.status as keyof typeof statusConfig];

                            return (
                                <tr
                                    key={user.id}
                                    className="hover:bg-accent/5 transition-colors"
                                >
                                    <td className="px-4 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-medium">
                                                {user.displayName.charAt(0)}
                                            </div>
                                            <div>
                                                <div className="font-medium text-foreground">
                                                    {user.displayName}
                                                </div>
                                                <div className="text-sm text-muted-foreground">
                                                    {user.username} • {user.email}
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-4 py-4">
                                        <div className="flex flex-wrap gap-1">
                                            {user.roles.map((role) => (
                                                <span
                                                    key={role}
                                                    className={`inline-flex px-2 py-1 rounded text-xs font-medium ${roleColors[role] || 'bg-muted text-muted-foreground'
                                                        }`}
                                                >
                                                    {roleLabels[role] || role}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="px-4 py-4">
                                        <span
                                            className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}
                                        >
                                            {status.label}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground">
                                        {user.lastLogin}
                                    </td>
                                    <td className="px-4 py-4 text-sm text-muted-foreground">
                                        {user.createdAt}
                                    </td>
                                    <td className="px-4 py-4">
                                        <div className="flex items-center gap-2">
                                            <button className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded cursor-pointer">
                                                <Edit className="h-4 w-4" />
                                            </button>
                                            <button className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded cursor-pointer">
                                                <Shield className="h-4 w-4" />
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
            </div>

            {/* 创建用户模态框 */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-md animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-4">新建用户</h2>
                        <form className="space-y-4">
                            <div>
                                <label className="label">用户名</label>
                                <input type="text" className="input mt-1" placeholder="请输入用户名" />
                            </div>
                            <div>
                                <label className="label">邮箱</label>
                                <input type="email" className="input mt-1" placeholder="请输入邮箱" />
                            </div>
                            <div>
                                <label className="label">姓名</label>
                                <input type="text" className="input mt-1" placeholder="请输入姓名" />
                            </div>
                            <div>
                                <label className="label">密码</label>
                                <input
                                    type="password"
                                    className="input mt-1"
                                    placeholder="请输入密码"
                                />
                            </div>
                            <div>
                                <label className="label">角色</label>
                                <select className="input mt-1">
                                    <option value="">请选择角色</option>
                                    <option value="admin">系统管理员</option>
                                    <option value="kb_admin">知识库管理员</option>
                                    <option value="cmdb_admin">CMDB管理员</option>
                                    <option value="alert_operator">告警处理员</option>
                                    <option value="viewer">只读用户</option>
                                </select>
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
