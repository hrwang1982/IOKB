'use client';

import { useState, useEffect, useCallback } from 'react';
import {
    Edit,
    Key,
    Plus,
    Search,
    Shield,
    Trash2,
    UserPlus,
    ToggleLeft,
    ToggleRight,
    X,
    Loader2,
} from 'lucide-react';
import {
    getUsers,
    createUserApi,
    updateUserApi,
    deleteUserApi,
    updateUserStatus,
    resetUserPassword,
    getRoles,
    type UserInfo,
    type RoleInfo,
} from '@/lib/api';

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
    disabled: { label: '禁用', className: 'bg-muted text-muted-foreground' },
    inactive: { label: '禁用', className: 'bg-muted text-muted-foreground' },
};

export default function UsersPage() {
    const [users, setUsers] = useState<UserInfo[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [page, setPage] = useState(1);
    const [roles, setRoles] = useState<RoleInfo[]>([]);

    // 模态框状态
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [showResetPwdModal, setShowResetPwdModal] = useState(false);

    const [selectedUser, setSelectedUser] = useState<UserInfo | null>(null);
    const [actionLoading, setActionLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMsg, setSuccessMsg] = useState('');

    // 创建表单
    const [createForm, setCreateForm] = useState({
        username: '',
        email: '',
        display_name: '',
        password: '',
        role_codes: [] as string[],
    });

    // 编辑表单
    const [editForm, setEditForm] = useState({
        email: '',
        display_name: '',
    });

    // 重置密码
    const [newPassword, setNewPassword] = useState('');

    // 加载用户列表
    const loadUsers = useCallback(async () => {
        setLoading(true);
        try {
            const res = await getUsers({
                page,
                size: 20,
                keyword: searchQuery || undefined,
            });
            setUsers(res.items);
            setTotal(res.total);
        } catch (err) {
            console.error('加载用户列表失败:', err);
        } finally {
            setLoading(false);
        }
    }, [page, searchQuery]);

    // 加载角色列表
    const loadRoles = useCallback(async () => {
        try {
            const res = await getRoles();
            setRoles(res.items);
        } catch (err) {
            console.error('加载角色列表失败:', err);
        }
    }, []);

    useEffect(() => {
        loadUsers();
    }, [loadUsers]);

    useEffect(() => {
        loadRoles();
    }, [loadRoles]);

    // 搜索防抖
    useEffect(() => {
        const timer = setTimeout(() => {
            setPage(1);
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const showSuccess = (msg: string) => {
        setSuccessMsg(msg);
        setTimeout(() => setSuccessMsg(''), 3000);
    };

    // 创建用户
    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setActionLoading(true);
        setError('');
        try {
            await createUserApi({
                username: createForm.username,
                password: createForm.password,
                email: createForm.email || undefined,
                display_name: createForm.display_name || undefined,
                role_codes: createForm.role_codes.length > 0 ? createForm.role_codes : undefined,
            });
            setShowCreateModal(false);
            setCreateForm({ username: '', email: '', display_name: '', password: '', role_codes: [] });
            showSuccess('用户创建成功');
            loadUsers();
        } catch (err: any) {
            setError(err.message || '创建失败');
        } finally {
            setActionLoading(false);
        }
    };

    // 编辑用户
    const handleEdit = (user: UserInfo) => {
        setSelectedUser(user);
        setEditForm({
            email: user.email || '',
            display_name: user.display_name || '',
        });
        setShowEditModal(true);
        setError('');
    };

    const handleEditSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedUser) return;
        setActionLoading(true);
        setError('');
        try {
            await updateUserApi(selectedUser.id, {
                email: editForm.email || undefined,
                display_name: editForm.display_name || undefined,
            });
            setShowEditModal(false);
            showSuccess('用户更新成功');
            loadUsers();
        } catch (err: any) {
            setError(err.message || '更新失败');
        } finally {
            setActionLoading(false);
        }
    };

    // 删除用户
    const handleDelete = (user: UserInfo) => {
        setSelectedUser(user);
        setShowDeleteConfirm(true);
    };

    const confirmDelete = async () => {
        if (!selectedUser) return;
        setActionLoading(true);
        try {
            await deleteUserApi(selectedUser.id);
            setShowDeleteConfirm(false);
            showSuccess('用户已删除');
            loadUsers();
        } catch (err: any) {
            setError(err.message || '删除失败');
        } finally {
            setActionLoading(false);
        }
    };

    // 切换状态
    const handleToggleStatus = async (user: UserInfo) => {
        const newStatus = user.status === 'active' ? 'disabled' : 'active';
        try {
            await updateUserStatus(user.id, newStatus);
            showSuccess(`用户已${newStatus === 'active' ? '启用' : '禁用'}`);
            loadUsers();
        } catch (err: any) {
            setError(err.message || '操作失败');
        }
    };

    // 重置密码
    const handleResetPwd = (user: UserInfo) => {
        setSelectedUser(user);
        setNewPassword('');
        setShowResetPwdModal(true);
        setError('');
    };

    const confirmResetPwd = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedUser) return;
        setActionLoading(true);
        setError('');
        try {
            await resetUserPassword(selectedUser.id, newPassword);
            setShowResetPwdModal(false);
            showSuccess('密码重置成功');
        } catch (err: any) {
            setError(err.message || '重置失败');
        } finally {
            setActionLoading(false);
        }
    };

    const activeCount = users.filter((u) => u.status === 'active').length;
    const adminCount = users.filter((u) => u.roles.includes('admin')).length;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 成功提示 */}
            {successMsg && (
                <div className="fixed top-4 right-4 z-50 bg-success/10 text-success px-4 py-3 rounded-lg shadow-lg border border-success/20 animate-slide-in">
                    {successMsg}
                </div>
            )}

            {/* 页面标题 */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">用户管理</h1>
                    <p className="text-muted-foreground mt-1">管理系统用户和权限</p>
                </div>
                <button
                    onClick={() => {
                        setShowCreateModal(true);
                        setError('');
                    }}
                    className="btn-primary flex items-center gap-2"
                >
                    <UserPlus className="h-4 w-4" />
                    新建用户
                </button>
            </div>

            {/* 统计概览 */}
            <div className="grid grid-cols-4 gap-4">
                {[
                    { label: '全部用户', value: total, color: 'primary' },
                    { label: '启用中', value: activeCount, color: 'success' },
                    { label: '管理员', value: adminCount, color: 'error' },
                    { label: '角色数', value: roles.length, color: 'accent' },
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
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-6 w-6 animate-spin text-primary" />
                        <span className="ml-2 text-muted-foreground">加载中...</span>
                    </div>
                ) : users.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                        暂无用户数据
                    </div>
                ) : (
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
                            {users.map((user) => {
                                const userStatus = statusConfig[user.status as keyof typeof statusConfig] || statusConfig.inactive;

                                return (
                                    <tr
                                        key={user.id}
                                        className="hover:bg-accent/5 transition-colors"
                                    >
                                        <td className="px-4 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-medium">
                                                    {(user.display_name || user.username).charAt(0)}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-foreground">
                                                        {user.display_name || user.username}
                                                    </div>
                                                    <div className="text-sm text-muted-foreground">
                                                        {user.username} • {user.email || '无邮箱'}
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
                                                {user.roles.length === 0 && (
                                                    <span className="text-xs text-muted-foreground">无角色</span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-4 py-4">
                                            <span
                                                className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${userStatus.className}`}
                                            >
                                                {userStatus.label}
                                            </span>
                                        </td>
                                        <td className="px-4 py-4 text-sm text-muted-foreground">
                                            {user.last_login_at
                                                ? new Date(user.last_login_at).toLocaleString('zh-CN')
                                                : '从未登录'}
                                        </td>
                                        <td className="px-4 py-4 text-sm text-muted-foreground">
                                            {user.created_at
                                                ? new Date(user.created_at).toLocaleString('zh-CN')
                                                : '-'}
                                        </td>
                                        <td className="px-4 py-4">
                                            <div className="flex items-center gap-1">
                                                <button
                                                    onClick={() => handleEdit(user)}
                                                    className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded cursor-pointer"
                                                    title="编辑"
                                                >
                                                    <Edit className="h-4 w-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleResetPwd(user)}
                                                    className="p-1.5 text-muted-foreground hover:text-warning hover:bg-warning/10 rounded cursor-pointer"
                                                    title="重置密码"
                                                >
                                                    <Key className="h-4 w-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleToggleStatus(user)}
                                                    className="p-1.5 text-muted-foreground hover:text-accent hover:bg-accent/10 rounded cursor-pointer"
                                                    title={user.status === 'active' ? '禁用' : '启用'}
                                                >
                                                    {user.status === 'active' ? (
                                                        <ToggleRight className="h-4 w-4 text-success" />
                                                    ) : (
                                                        <ToggleLeft className="h-4 w-4" />
                                                    )}
                                                </button>
                                                {user.username !== 'admin' && (
                                                    <button
                                                        onClick={() => handleDelete(user)}
                                                        className="p-1.5 text-muted-foreground hover:text-error hover:bg-error/10 rounded cursor-pointer"
                                                        title="删除"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                )}
            </div>

            {/* 分页 */}
            {total > 20 && (
                <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">共 {total} 条</span>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="btn-outline text-sm disabled:opacity-50"
                        >
                            上一页
                        </button>
                        <span className="flex items-center px-3 text-sm text-muted-foreground">
                            {page} / {Math.ceil(total / 20)}
                        </span>
                        <button
                            onClick={() => setPage((p) => p + 1)}
                            disabled={page * 20 >= total}
                            className="btn-outline text-sm disabled:opacity-50"
                        >
                            下一页
                        </button>
                    </div>
                </div>
            )}

            {/* 创建用户模态框 */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-md animate-slide-in">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-foreground">新建用户</h2>
                            <button onClick={() => setShowCreateModal(false)} className="text-muted-foreground hover:text-foreground cursor-pointer">
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                        {error && <div className="mb-4 p-3 rounded-md bg-error/10 text-error text-sm">{error}</div>}
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div>
                                <label className="label">用户名 *</label>
                                <input
                                    type="text"
                                    className="input mt-1"
                                    placeholder="请输入用户名"
                                    value={createForm.username}
                                    onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label className="label">邮箱</label>
                                <input
                                    type="email"
                                    className="input mt-1"
                                    placeholder="请输入邮箱"
                                    value={createForm.email}
                                    onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="label">姓名</label>
                                <input
                                    type="text"
                                    className="input mt-1"
                                    placeholder="请输入显示名称"
                                    value={createForm.display_name}
                                    onChange={(e) => setCreateForm({ ...createForm, display_name: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="label">密码 *</label>
                                <input
                                    type="password"
                                    className="input mt-1"
                                    placeholder="请输入密码"
                                    value={createForm.password}
                                    onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label className="label">角色</label>
                                <select
                                    className="input mt-1"
                                    value={createForm.role_codes[0] || ''}
                                    onChange={(e) =>
                                        setCreateForm({
                                            ...createForm,
                                            role_codes: e.target.value ? [e.target.value] : [],
                                        })
                                    }
                                >
                                    <option value="">请选择角色</option>
                                    {roles.map((role) => (
                                        <option key={role.code} value={role.code}>
                                            {role.name}
                                        </option>
                                    ))}
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
                                <button type="submit" className="btn-primary flex-1" disabled={actionLoading}>
                                    {actionLoading ? '创建中...' : '创建'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* 编辑用户模态框 */}
            {showEditModal && selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-md animate-slide-in">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-foreground">
                                编辑用户 - {selectedUser.username}
                            </h2>
                            <button onClick={() => setShowEditModal(false)} className="text-muted-foreground hover:text-foreground cursor-pointer">
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                        {error && <div className="mb-4 p-3 rounded-md bg-error/10 text-error text-sm">{error}</div>}
                        <form onSubmit={handleEditSubmit} className="space-y-4">
                            <div>
                                <label className="label">邮箱</label>
                                <input
                                    type="email"
                                    className="input mt-1"
                                    placeholder="请输入邮箱"
                                    value={editForm.email}
                                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="label">显示名称</label>
                                <input
                                    type="text"
                                    className="input mt-1"
                                    placeholder="请输入显示名称"
                                    value={editForm.display_name}
                                    onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setShowEditModal(false)}
                                    className="btn-outline flex-1"
                                >
                                    取消
                                </button>
                                <button type="submit" className="btn-primary flex-1" disabled={actionLoading}>
                                    {actionLoading ? '保存中...' : '保存'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* 删除确认模态框 */}
            {showDeleteConfirm && selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-sm animate-slide-in">
                        <h2 className="text-lg font-semibold text-foreground mb-2">确认删除</h2>
                        <p className="text-muted-foreground mb-6">
                            确定要删除用户 <strong>{selectedUser.display_name || selectedUser.username}</strong> 吗？此操作不可撤销。
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowDeleteConfirm(false)}
                                className="btn-outline flex-1"
                            >
                                取消
                            </button>
                            <button
                                onClick={confirmDelete}
                                className="btn-primary flex-1 !bg-error hover:!bg-error/90"
                                disabled={actionLoading}
                            >
                                {actionLoading ? '删除中...' : '确认删除'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 重置密码模态框 */}
            {showResetPwdModal && selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="card p-6 w-full max-w-sm animate-slide-in">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-foreground">
                                重置密码 - {selectedUser.username}
                            </h2>
                            <button onClick={() => setShowResetPwdModal(false)} className="text-muted-foreground hover:text-foreground cursor-pointer">
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                        {error && <div className="mb-4 p-3 rounded-md bg-error/10 text-error text-sm">{error}</div>}
                        <form onSubmit={confirmResetPwd} className="space-y-4">
                            <div>
                                <label className="label">新密码</label>
                                <input
                                    type="password"
                                    className="input mt-1"
                                    placeholder="请输入新密码"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setShowResetPwdModal(false)}
                                    className="btn-outline flex-1"
                                >
                                    取消
                                </button>
                                <button type="submit" className="btn-primary flex-1" disabled={actionLoading}>
                                    {actionLoading ? '重置中...' : '确认重置'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
