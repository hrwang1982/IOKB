'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Lock, User } from 'lucide-react';
import { ThemeToggle } from '@/components/theme-toggle';

export default function LoginPage() {
    const router = useRouter();
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        username: '',
        password: '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            // 调用后端登录API
            const response = await fetch('http://localhost:8000/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: formData.username,
                    password: formData.password,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || '登录失败');
            }

            const data = await response.json();

            // 存储Token到localStorage
            if (data.access_token) {
                localStorage.setItem('token', data.access_token);
            }

            // 登录成功，跳转到仪表盘
            router.push('/dashboard');
        } catch (err) {
            setError(err instanceof Error ? err.message : '用户名或密码错误');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            {/* 主题切换 */}
            <div className="absolute top-4 right-4">
                <ThemeToggle />
            </div>

            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-2xl mb-4">
                        <span className="text-2xl font-bold text-white">IOKB</span>
                    </div>
                    <h1 className="text-2xl font-bold text-foreground">智能运维知识库</h1>
                    <p className="text-muted-foreground mt-2">登录以继续使用系统</p>
                </div>

                {/* 登录表单 */}
                <div className="card p-8">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="p-3 rounded-md bg-error/10 text-error text-sm">
                                {error}
                            </div>
                        )}

                        {/* 用户名 */}
                        <div className="space-y-2">
                            <label htmlFor="username" className="label">
                                用户名
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <input
                                    id="username"
                                    type="text"
                                    placeholder="请输入用户名"
                                    className="input pl-10"
                                    value={formData.username}
                                    onChange={(e) =>
                                        setFormData({ ...formData, username: e.target.value })
                                    }
                                    required
                                />
                            </div>
                        </div>

                        {/* 密码 */}
                        <div className="space-y-2">
                            <label htmlFor="password" className="label">
                                密码
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="请输入密码"
                                    className="input pl-10 pr-10"
                                    value={formData.password}
                                    onChange={(e) =>
                                        setFormData({ ...formData, password: e.target.value })
                                    }
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground cursor-pointer"
                                >
                                    {showPassword ? (
                                        <EyeOff className="h-4 w-4" />
                                    ) : (
                                        <Eye className="h-4 w-4" />
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* 登录按钮 */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-primary w-full h-11"
                        >
                            {loading ? (
                                <span className="flex items-center gap-2">
                                    <svg
                                        className="animate-spin h-4 w-4"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                    >
                                        <circle
                                            className="opacity-25"
                                            cx="12"
                                            cy="12"
                                            r="10"
                                            stroke="currentColor"
                                            strokeWidth="4"
                                        />
                                        <path
                                            className="opacity-75"
                                            fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                                        />
                                    </svg>
                                    登录中...
                                </span>
                            ) : (
                                '登 录'
                            )}
                        </button>
                    </form>

                    {/* SSO 登录 */}
                    <div className="mt-6">
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-border" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-card text-muted-foreground">
                                    或使用其他方式
                                </span>
                            </div>
                        </div>

                        <div className="mt-6 grid grid-cols-2 gap-3">
                            <button
                                type="button"
                                className="btn-outline h-11"
                                onClick={() => {
                                    // TODO: SSO登录
                                }}
                            >
                                LDAP 登录
                            </button>
                            <button
                                type="button"
                                className="btn-outline h-11"
                                onClick={() => {
                                    // TODO: SSO登录
                                }}
                            >
                                SSO 登录
                            </button>
                        </div>
                    </div>
                </div>

                {/* 版权信息 */}
                <p className="text-center text-sm text-muted-foreground mt-8">
                    © 2026 IOKB 智能运维知识库. All rights reserved.
                </p>
            </div>
        </div>
    );
}
