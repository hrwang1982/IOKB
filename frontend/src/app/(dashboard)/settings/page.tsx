'use client';

import { useState, useEffect } from 'react';
import {
    Bell,
    Check,
    Code,
    Database,
    FileText,
    Loader,
    RotateCcw,
    Save,
    Settings,
    Shield,
    Sparkles,
    X,
} from 'lucide-react';

// 配置文件类型
type ConfigFile = {
    code: string;
    name: string;
    path: string;
    description: string;
    content?: string;
};

const configIcons: Record<string, typeof FileText> = {
    cmdb: Database,
    alert: Bell,
    rag: Sparkles,
    auth: Shield,
};

export default function SettingsPage() {
    const [configs, setConfigs] = useState<ConfigFile[]>([]);
    const [selectedConfig, setSelectedConfig] = useState<ConfigFile | null>(null);
    const [content, setContent] = useState('');
    const [originalContent, setOriginalContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [validating, setValidating] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    // 获取配置文件列表
    useEffect(() => {
        fetchConfigs();
    }, []);

    const fetchConfigs = async () => {
        try {
            setLoading(true);
            const res = await fetch('/api/v1/system/configs');
            if (res.ok) {
                const data = await res.json();
                setConfigs(data);
                if (data.length > 0) {
                    await loadConfigContent(data[0]);
                }
            } else {
                showMessage('error', '获取配置列表失败');
            }
        } catch (error) {
            showMessage('error', '网络错误，获取配置列表失败');
        } finally {
            setLoading(false);
        }
    };

    const loadConfigContent = async (config: ConfigFile) => {
        try {
            setLoading(true);
            const res = await fetch(`/api/v1/system/configs/${config.code}`);
            if (res.ok) {
                const data = await res.json();
                setSelectedConfig(data);
                setContent(data.content);
                setOriginalContent(data.content);
            } else {
                showMessage('error', `读取配置 ${config.name} 失败`);
            }
        } catch (error) {
            showMessage('error', '网络错误，读取配置失败');
        } finally {
            setLoading(false);
        }
    };

    const handleConfigChange = (config: ConfigFile) => {
        if (content !== originalContent) {
            if (!confirm('当前配置未保存，是否切换？')) {
                return;
            }
        }
        loadConfigContent(config);
    };

    const handleValidate = async () => {
        if (!selectedConfig) return;

        setValidating(true);
        try {
            const res = await fetch(`/api/v1/system/configs/${selectedConfig.code}/validate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content }),
            });
            const data = await res.json();
            if (data.valid) {
                showMessage('success', 'YAML 格式正确');
            } else {
                showMessage('error', data.message);
            }
        } catch (error) {
            showMessage('error', '验证失败');
        } finally {
            setValidating(false);
        }
    };

    const handleSave = async () => {
        if (!selectedConfig) return;

        setSaving(true);
        try {
            const res = await fetch(`/api/v1/system/configs/${selectedConfig.code}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content }),
            });

            if (res.ok) {
                const data = await res.json();
                setOriginalContent(content);
                showMessage('success', data.message || '保存成功');
            } else {
                const error = await res.json();
                showMessage('error', error.detail || '保存失败');
            }
        } catch (error) {
            showMessage('error', '网络错误，保存失败');
        } finally {
            setSaving(false);
        }
    };

    const handleRestore = async () => {
        if (!selectedConfig) return;
        if (!confirm('确定要从备份恢复配置吗？当前内容将被覆盖。')) return;

        try {
            const res = await fetch(`/api/v1/system/configs/${selectedConfig.code}/restore`, {
                method: 'POST',
            });

            if (res.ok) {
                showMessage('success', '已从备份恢复');
                await loadConfigContent(selectedConfig);
            } else {
                const error = await res.json();
                showMessage('error', error.detail || '恢复失败');
            }
        } catch (error) {
            showMessage('error', '网络错误，恢复失败');
        }
    };

    const showMessage = (type: 'success' | 'error', text: string) => {
        setMessage({ type, text });
        setTimeout(() => setMessage(null), 5000);
    };

    const hasChanges = content !== originalContent;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* 页面标题 */}
            <div>
                <h1 className="text-2xl font-bold text-foreground">系统设置</h1>
                <p className="text-muted-foreground mt-1">管理系统配置和参数</p>
            </div>

            {/* 消息提示 */}
            {message && (
                <div
                    className={`p-4 rounded-lg flex items-center gap-3 ${message.type === 'success'
                            ? 'bg-green-500/10 text-green-500 border border-green-500/20'
                            : 'bg-red-500/10 text-red-500 border border-red-500/20'
                        }`}
                >
                    {message.type === 'success' ? (
                        <Check className="h-5 w-5" />
                    ) : (
                        <X className="h-5 w-5" />
                    )}
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* 配置文件列表 */}
                <div className="lg:col-span-1 space-y-2">
                    {loading && configs.length === 0 ? (
                        <div className="flex items-center justify-center p-8">
                            <Loader className="h-6 w-6 animate-spin text-primary" />
                        </div>
                    ) : (
                        configs.map((config) => {
                            const Icon = configIcons[config.code] || FileText;
                            const isActive = selectedConfig?.code === config.code;

                            return (
                                <button
                                    key={config.code}
                                    onClick={() => handleConfigChange(config)}
                                    className={`w-full text-left p-4 rounded-lg border transition-colors cursor-pointer ${isActive
                                            ? 'bg-primary/10 border-primary text-primary'
                                            : 'bg-card border-border hover:border-primary/50'
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <Icon className="h-5 w-5 shrink-0" />
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium truncate">{config.name}</div>
                                            <div className="text-xs text-muted-foreground truncate mt-0.5">
                                                {config.path}
                                            </div>
                                        </div>
                                    </div>
                                </button>
                            );
                        })
                    )}
                </div>

                {/* 配置编辑器 */}
                <div className="lg:col-span-3 space-y-4">
                    {selectedConfig ? (
                        <>
                            {/* 编辑器头部 */}
                            <div className="card p-4">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
                                            {selectedConfig.name}
                                            {hasChanges && (
                                                <span className="text-xs px-2 py-0.5 bg-warning/10 text-warning rounded">
                                                    未保存
                                                </span>
                                            )}
                                        </h2>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            {selectedConfig.description}
                                        </p>
                                        <p className="text-xs text-muted-foreground mt-2 font-mono">
                                            {selectedConfig.path}
                                        </p>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={handleValidate}
                                            disabled={validating}
                                            className="btn-outline flex items-center gap-2"
                                        >
                                            {validating ? (
                                                <Loader className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <Code className="h-4 w-4" />
                                            )}
                                            验证
                                        </button>
                                        <button
                                            onClick={handleSave}
                                            disabled={saving || !hasChanges}
                                            className="btn-primary flex items-center gap-2"
                                        >
                                            {saving ? (
                                                <Loader className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <Save className="h-4 w-4" />
                                            )}
                                            保存配置
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* 代码编辑器 */}
                            <div className="card overflow-hidden">
                                <div className="bg-slate-900 dark:bg-slate-950 p-4 font-mono text-sm">
                                    {loading ? (
                                        <div className="flex items-center justify-center py-20">
                                            <Loader className="h-8 w-8 animate-spin text-primary" />
                                        </div>
                                    ) : (
                                        <textarea
                                            value={content}
                                            onChange={(e) => setContent(e.target.value)}
                                            className="w-full min-h-[500px] bg-transparent text-slate-100 resize-none focus:outline-none"
                                            spellCheck={false}
                                            style={{ fontFamily: "'JetBrains Mono', monospace" }}
                                        />
                                    )}
                                </div>
                            </div>

                            {/* 提示信息 */}
                            <div className="card p-4 bg-warning/5 border-warning/20">
                                <div className="flex gap-3">
                                    <Settings className="h-5 w-5 text-warning shrink-0 mt-0.5" />
                                    <div className="text-sm text-muted-foreground">
                                        <p className="font-medium text-warning mb-1">配置修改注意事项</p>
                                        <ul className="space-y-1 list-disc list-inside">
                                            <li>修改配置后需要重启相应服务才能生效</li>
                                            <li>请确保YAML格式正确，否则可能导致服务无法启动</li>
                                            <li>系统会自动备份历史配置版本</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>

                            {/* 快捷操作 */}
                            <div className="grid grid-cols-3 gap-4">
                                <button
                                    onClick={handleValidate}
                                    className="card p-4 hover:border-primary/50 transition-colors cursor-pointer text-left"
                                >
                                    <Code className="h-5 w-5 text-primary mb-2" />
                                    <div className="font-medium text-foreground">验证配置</div>
                                    <div className="text-sm text-muted-foreground">检查YAML语法</div>
                                </button>
                                <button
                                    onClick={handleRestore}
                                    className="card p-4 hover:border-primary/50 transition-colors cursor-pointer text-left"
                                >
                                    <RotateCcw className="h-5 w-5 text-accent mb-2" />
                                    <div className="font-medium text-foreground">恢复备份</div>
                                    <div className="text-sm text-muted-foreground">从上次保存恢复</div>
                                </button>
                                <button
                                    onClick={() => {
                                        setContent(originalContent);
                                        showMessage('success', '已撤销更改');
                                    }}
                                    disabled={!hasChanges}
                                    className="card p-4 hover:border-primary/50 transition-colors cursor-pointer text-left disabled:opacity-50"
                                >
                                    <X className="h-5 w-5 text-red-500 mb-2" />
                                    <div className="font-medium text-foreground">撤销更改</div>
                                    <div className="text-sm text-muted-foreground">还原未保存的修改</div>
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="card p-20 text-center text-muted-foreground">
                            {loading ? (
                                <Loader className="h-8 w-8 animate-spin mx-auto" />
                            ) : (
                                '请从左侧选择配置文件'
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
