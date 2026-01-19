'use client';

import { useState } from 'react';
import {
    Check,
    Edit,
    MoreVertical,
    Plus,
    Shield,
    Trash2,
    X,
} from 'lucide-react';

// 模拟角色数据
const mockRoles = [
    {
        id: 1,
        name: '系统管理员',
        code: 'admin',
        description: '拥有系统所有权限，可以管理用户、角色和系统配置',
        userCount: 1,
        permissions: ['*:*'],
        createdAt: '2026-01-01 10:00:00',
    },
    {
        id: 2,
        name: '知识库管理员',
        code: 'kb_admin',
        description: '管理知识库内容，包括文档上传、编辑和删除',
        userCount: 3,
        permissions: ['kb:create', 'kb:read', 'kb:write', 'kb:delete'],
        createdAt: '2026-01-01 10:00:00',
    },
    {
        id: 3,
        name: 'CMDB管理员',
        code: 'cmdb_admin',
        description: '管理配置项，维护CMDB数据',
        userCount: 2,
        permissions: ['cmdb:create', 'cmdb:read', 'cmdb:write', 'cmdb:delete'],
        createdAt: '2026-01-01 10:00:00',
    },
    {
        id: 4,
        name: '告警处理员',
        code: 'alert_operator',
        description: '处理和响应告警事件',
        userCount: 5,
        permissions: ['alert:read', 'alert:ack', 'alert:resolve'],
        createdAt: '2026-01-01 10:00:00',
    },
    {
        id: 5,
        name: '只读用户',
        code: 'viewer',
        description: '只能查看系统信息，不能进行任何修改',
        userCount: 10,
        permissions: ['kb:read', 'cmdb:read', 'alert:read'],
        createdAt: '2026-01-01 10:00:00',
    },
];

// 所有权限
const allPermissions = [
    { module: '知识库', permissions: ['kb:create', 'kb:read', 'kb:write', 'kb:delete'] },
    { module: 'CMDB', permissions: ['cmdb:create', 'cmdb:read', 'cmdb:write', 'cmdb:delete'] },
    { module: '告警', permissions: ['alert:read', 'alert:ack', 'alert:resolve', 'alert:manage'] },
    { module: '用户', permissions: ['user:create', 'user:read', 'user:write', 'user:delete'] },
    { module: '系统', permissions: ['system:config', 'system:audit'] },
];

const permissionLabels: Record<string, string> = {
    create: '创建',
    read: '读取',
    write: '编辑',
    delete: '删除',
    ack: '确认',
    resolve: '解决',
    manage: '管理',
    config: '配置',
    audit: '审计',
};

export default function RolesPage() {
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showPermissionModal, setShowPermissionModal] = useState(false);
    const [selectedRole, setSelectedRole] = useState<typeof mockRoles[0] | null>(null);

    const handleEditPermissions = (role: typeof mockRoles[0]) => {
        setSelectedRole(role);
        setShowPermissionModal(true);
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 页面标题 */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">角色权限管理</h1>
                    <p className="text-muted-foreground mt-1">管理系统角色和权限分配</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus className="h-4 w-4" />
                    新建角色
                </button>
            </div>

            {/* 统计概览 */}
            <div className="grid grid-cols-4 gap-4">
                {[
                    { label: '全部角色', value: mockRoles.length, color: 'primary' },
                    { label: '系统预置', value: 5, color: 'accent' },
                    {
                        label: '总用户数',
                        value: mockRoles.reduce((sum, r) => sum + r.userCount, 0),
                        color: 'success',
                    },
                    { label: '权限总数', value: 22, color: 'warning' },
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

            {/* 角色列表 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mockRoles.map((role) => (
                    <div key={role.id} className="card p-6 hover:border-primary/50 transition-colors">
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className="p-3 rounded-lg bg-primary/10 text-primary">
                                    <Shield className="h-6 w-6" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground">{role.name}</h3>
                                    <p className="text-sm text-muted-foreground">
                                        <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                                            {role.code}
                                        </code>
                                    </p>
                                </div>
                            </div>
                            <button className="p-1.5 text-muted-foreground hover:bg-accent/10 hover:text-accent rounded cursor-pointer">
                                <MoreVertical className="h-5 w-5" />
                            </button>
                        </div>

                        <p className="text-sm text-muted-foreground mb-4">{role.description}</p>

                        <div className="mb-4">
                            <div className="text-xs text-muted-foreground mb-2">权限 ({role.permissions.length})</div>
                            <div className="flex flex-wrap gap-1">
                                {role.permissions.slice(0, 6).map((perm, idx) => (
                                    <span
                                        key={idx}
                                        className="inline-flex px-2 py-1 bg-muted text-muted-foreground rounded text-xs"
                                    >
                                        {perm === '*:*' ? '全部权限' : perm}
                                    </span>
                                ))}
                                {role.permissions.length > 6 && (
                                    <span className="inline-flex px-2 py-1 bg-muted text-muted-foreground rounded text-xs">
                                        +{role.permissions.length - 6}
                                    </span>
                                )}
                            </div>
                        </div>

                        <div className="pt-4 border-t border-border flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">
                                {role.userCount} 个用户
                            </span>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleEditPermissions(role)}
                                    className="btn-outline text-sm"
                                >
                                    <Shield className="h-4 w-4 mr-1" />
                                    编辑权限
                                </button>
                                {role.code !== 'admin' && (
                                    <button className="btn-ghost p-2 text-error hover:bg-error/10">
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* 权限编辑模态框 */}
            {showPermissionModal && selectedRole && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-4">
                            编辑权限 - {selectedRole.name}
                        </h2>
                        <div className="space-y-4">
                            {allPermissions.map((module) => (
                                <div key={module.module} className="border border-border rounded-lg p-4">
                                    <h3 className="font-medium text-foreground mb-3">{module.module}</h3>
                                    <div className="grid grid-cols-2 gap-2">
                                        {module.permissions.map((perm) => {
                                            const [, action] = perm.split(':');
                                            const isSelected = selectedRole.permissions.includes(perm) || selectedRole.permissions.includes('*:*');

                                            return (
                                                <label
                                                    key={perm}
                                                    className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${isSelected
                                                            ? 'bg-primary/10 text-primary'
                                                            : 'hover:bg-muted'
                                                        }`}
                                                >
                                                    <div className={`w-4 h-4 rounded border flex items-center justify-center ${isSelected
                                                            ? 'bg-primary border-primary'
                                                            : 'border-border'
                                                        }`}>
                                                        {isSelected && <Check className="h-3 w-3 text-white" />}
                                                    </div>
                                                    <span className="text-sm">
                                                        {permissionLabels[action] || action}
                                                    </span>
                                                </label>
                                            );
                                        })}
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="flex gap-3 pt-6">
                            <button
                                onClick={() => setShowPermissionModal(false)}
                                className="btn-outline flex-1"
                            >
                                取消
                            </button>
                            <button
                                onClick={() => setShowPermissionModal(false)}
                                className="btn-primary flex-1"
                            >
                                保存
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 创建角色模态框 */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-md animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-4">新建角色</h2>
                        <form className="space-y-4">
                            <div>
                                <label className="label">角色名称</label>
                                <input type="text" className="input mt-1" placeholder="请输入角色名称" />
                            </div>
                            <div>
                                <label className="label">角色代码</label>
                                <input type="text" className="input mt-1" placeholder="请输入角色代码" />
                            </div>
                            <div>
                                <label className="label">描述</label>
                                <textarea
                                    className="input mt-1 min-h-[100px]"
                                    placeholder="请输入角色描述"
                                />
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
