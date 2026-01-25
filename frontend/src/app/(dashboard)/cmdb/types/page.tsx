'use client';

import { useEffect, useState } from 'react';
import {
    Edit,
    Plus,
    Trash2,
    Settings,
    ChevronDown,
    ChevronRight,
    Server,
    Database,
    Network,
    Box,
    Loader2
} from 'lucide-react';
import { getCITypes, createCIType, updateCIType, deleteCIType, type CIType, type AttributeDefinition } from '@/lib/api';

// 图标映射
const iconMap: Record<string, any> = {
    server: Server,
    database: Database,
    network: Network,
    default: Box
};

export default function CITypesPage() {
    const [types, setTypes] = useState<CIType[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});

    // 表单状态
    const [showModal, setShowModal] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [currentCode, setCurrentCode] = useState('');
    const [formData, setFormData] = useState({
        name: '',
        code: '',
        icon: 'default',
        description: '',
        category: 'custom',
        attributes: [] as AttributeDefinition[]
    });

    // 加载数据
    const loadTypes = async () => {
        setLoading(true);
        try {
            const res = await getCITypes();
            setTypes(res.items);

            // 默认展开所有分类
            const categories: Record<string, boolean> = {};
            res.items.forEach(t => {
                const cat = t.category || '未分类';
                categories[cat] = true;
            });
            setExpandedCategories(prev => ({ ...categories, ...prev }));
        } catch (error) {
            console.error('Failed to load types:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadTypes();
    }, []);

    // 按分类分组
    const groupedTypes = types.reduce((acc, type) => {
        const cat = type.attribute_schema?.category || type.category || '未分类';
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(type);
        return acc;
    }, {} as Record<string, CIType[]>);

    const toggleCategory = (cat: string) => {
        setExpandedCategories(prev => ({
            ...prev,
            [cat]: !prev[cat]
        }));
    };

    // 处理表单
    const handleOpenCreate = () => {
        setIsEditing(false);
        setFormData({
            name: '',
            code: '',
            icon: 'default',
            description: '',
            category: 'custom',
            attributes: []
        });
        setShowModal(true);
    };

    const handleOpenEdit = (type: CIType) => {
        setIsEditing(true);
        setCurrentCode(type.code);
        setFormData({
            name: type.name,
            code: type.code,
            icon: type.icon || 'default',
            description: type.description || '',
            category: type.attribute_schema?.category || type.category || 'custom',
            attributes: type.attribute_schema?.attributes || []
        });
        setShowModal(true);
    };

    const handleSubmit = async () => {
        try {
            const payload = {
                name: formData.name,
                code: formData.code, // 编辑时后端可能忽略code修改，或者不允许修改
                icon: formData.icon,
                description: formData.description,
                attribute_schema: {
                    category: formData.category,
                    attributes: formData.attributes
                }
            };

            if (isEditing) {
                await updateCIType(currentCode, payload);
            } else {
                await createCIType(payload as any);
            }

            setShowModal(false);
            loadTypes();
        } catch (error) {
            alert('操作失败: ' + (error as Error).message);
        }
    };

    const handleDelete = async (code: string) => {
        if (!confirm('确定要删除这个类型吗？如果该类型下有配置项，删除将失败。')) return;
        try {
            await deleteCIType(code);
            loadTypes();
        } catch (error) {
            alert('删除失败: ' + (error as Error).message);
        }
    };

    // 简易属性编辑器
    const addAttribute = () => {
        setFormData(prev => ({
            ...prev,
            attributes: [
                ...prev.attributes,
                { name: '', label: '', type: 'string', required: false, default: null, options: null, description: '' }
            ]
        }));
    };

    const removeAttribute = (index: number) => {
        setFormData(prev => ({
            ...prev,
            attributes: prev.attributes.filter((_, i) => i !== index)
        }));
    };

    const updateAttribute = (index: number, field: keyof AttributeDefinition, value: any) => {
        setFormData(prev => ({
            ...prev,
            attributes: prev.attributes.map((attr, i) =>
                i === index ? { ...attr, [field]: value } : attr
            )
        }));
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">配置项类型管理</h1>
                    <p className="text-muted-foreground mt-1">定义和管理CMDB配置项的模型与属性</p>
                </div>
                <button
                    onClick={handleOpenCreate}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus className="h-4 w-4" />
                    新建类型
                </button>
            </div>

            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            ) : (
                <div className="space-y-4">
                    {Object.entries(groupedTypes).map(([category, items]) => (
                        <div key={category} className="card overflow-hidden">
                            <div
                                className="p-4 bg-muted/30 flex items-center justify-between cursor-pointer hover:bg-muted/50 transition-colors"
                                onClick={() => toggleCategory(category)}
                            >
                                <div className="flex items-center gap-2 font-medium">
                                    {expandedCategories[category] ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                                    {category}
                                    <span className="text-xs bg-muted px-2 py-0.5 rounded text-muted-foreground">{items.length}</span>
                                </div>
                            </div>

                            {expandedCategories[category] && (
                                <div className="divide-y divide-border">
                                    {items.map(type => {
                                        const Icon = iconMap[type.icon || 'default'] || Box;
                                        return (
                                            <div key={type.id} className="p-4 flex items-center justify-between hover:bg-accent/5 transition-colors group">
                                                <div className="flex items-center gap-4">
                                                    <div className="p-2 rounded bg-primary/10 text-primary">
                                                        <Icon className="h-5 w-5" />
                                                    </div>
                                                    <div>
                                                        <div className="font-medium flex items-center gap-2">
                                                            {type.name}
                                                            <code className="text-xs bg-muted px-1.5 py-0.5 rounded text-muted-foreground">{type.code}</code>
                                                        </div>
                                                        <div className="text-sm text-muted-foreground mt-0.5">
                                                            {type.description || '无描述'} • {type.attribute_schema?.attributes.length || 0} 个属性
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => handleOpenEdit(type)}
                                                        className="btn-ghost btn-sm"
                                                        title="编辑"
                                                    >
                                                        <Edit className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(type.code)}
                                                        className="btn-ghost btn-sm text-error hover:text-error hover:bg-error/10"
                                                        title="删除"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* 编辑/新建弹窗 */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto pt-10 pb-10">
                    <div className="card w-full max-w-3xl animate-slide-in flex flex-col max-h-[90vh]">
                        <div className="p-6 border-b border-border flex justify-between items-center bg-card sticky top-0 z-10 rounded-t-lg">
                            <h2 className="text-lg font-semibold">{isEditing ? '编辑类型' : '新建类型'}</h2>
                            <button onClick={() => setShowModal(false)} className="text-muted-foreground hover:text-foreground">✕</button>
                        </div>

                        <div className="p-6 overflow-y-auto flex-1">
                            <div className="space-y-6">
                                {/* 基础信息 */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">类型名称 *</label>
                                        <input
                                            className="input w-full"
                                            value={formData.name}
                                            onChange={e => setFormData({ ...formData, name: e.target.value })}
                                            placeholder="如: 负载均衡器"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">类型编码 * {isEditing && '(不可修改)'}</label>
                                        <input
                                            className="input w-full"
                                            value={formData.code}
                                            onChange={e => setFormData({ ...formData, code: e.target.value })}
                                            placeholder="如: lb"
                                            disabled={isEditing}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">分类</label>
                                        <input
                                            className="input w-full"
                                            value={formData.category}
                                            onChange={e => setFormData({ ...formData, category: e.target.value })}
                                            placeholder="如: 网络设备"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">图标</label>
                                        <select
                                            className="input w-full"
                                            value={formData.icon}
                                            onChange={e => setFormData({ ...formData, icon: e.target.value })}
                                        >
                                            <option value="default">默认</option>
                                            <option value="server">服务器</option>
                                            <option value="database">数据库</option>
                                            <option value="network">网络</option>
                                        </select>
                                    </div>
                                    <div className="col-span-2">
                                        <label className="block text-sm font-medium mb-1">描述</label>
                                        <textarea
                                            className="input w-full min-h-[60px]"
                                            value={formData.description}
                                            onChange={e => setFormData({ ...formData, description: e.target.value })}
                                        />
                                    </div>
                                </div>

                                {/* 属性定义 */}
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <h3 className="font-medium">属性定义</h3>
                                        <button onClick={addAttribute} className="btn-outline btn-sm gap-1">
                                            <Plus className="h-3 w-3" /> 添加属性
                                        </button>
                                    </div>
                                    <div className="space-y-2">
                                        {formData.attributes.map((attr, idx) => (
                                            <div key={idx} className="flex gap-2 items-start p-3 border border-border rounded-lg bg-muted/10">
                                                <div className="grid grid-cols-6 gap-2 flex-1">
                                                    <div className="col-span-1">
                                                        <input
                                                            className="input w-full text-xs"
                                                            placeholder="属性名 (英)"
                                                            value={attr.name}
                                                            onChange={e => updateAttribute(idx, 'name', e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-span-1">
                                                        <input
                                                            className="input w-full text-xs"
                                                            placeholder="标签 (中)"
                                                            value={attr.label}
                                                            onChange={e => updateAttribute(idx, 'label', e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-span-1">
                                                        <select
                                                            className="input w-full text-xs"
                                                            value={attr.type}
                                                            onChange={e => updateAttribute(idx, 'type', e.target.value)}
                                                        >
                                                            <option value="string">文本</option>
                                                            <option value="number">数字</option>
                                                            <option value="boolean">布尔</option>
                                                            <option value="date">日期</option>
                                                            <option value="enum">枚举</option>
                                                            <option value="json">JSON</option>
                                                        </select>
                                                    </div>
                                                    <div className="col-span-2">
                                                        <input
                                                            className="input w-full text-xs"
                                                            placeholder="描述"
                                                            value={attr.description}
                                                            onChange={e => updateAttribute(idx, 'description', e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="col-span-1 flex items-center justify-center">
                                                        <label className="flex items-center gap-1 text-xs cursor-pointer">
                                                            <input
                                                                type="checkbox"
                                                                checked={attr.required}
                                                                onChange={e => updateAttribute(idx, 'required', e.target.checked)}
                                                            /> 必填
                                                        </label>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => removeAttribute(idx)}
                                                    className="text-muted-foreground hover:text-error p-1"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </button>
                                            </div>
                                        ))}
                                        {formData.attributes.length === 0 && (
                                            <div className="text-center text-sm text-muted-foreground py-4 border border-dashed border-border rounded">
                                                暂无自定义属性
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 border-t border-border bg-card sticky bottom-0 z-10 rounded-b-lg flex gap-3">
                            <button onClick={() => setShowModal(false)} className="btn-outline flex-1">取消</button>
                            <button onClick={handleSubmit} className="btn-primary flex-1">保存</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
