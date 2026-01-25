import React, { useState, useEffect } from 'react';
import { type AttributeSchema, type AttributeDefinition } from '@/lib/api';
import { ChevronDown, Calendar, Search, User } from 'lucide-react';

interface DynamicFormProps {
    schema?: AttributeSchema | null;
    initialValues?: Record<string, any>;
    onChange: (values: Record<string, any>) => void;
    mode?: 'create' | 'edit' | 'view';
}

export function DynamicForm({ schema, initialValues = {}, onChange, mode = 'create' }: DynamicFormProps) {
    const [values, setValues] = useState<Record<string, any>>(initialValues);
    const [activeGroup, setActiveGroup] = useState<string>('');

    useEffect(() => {
        setValues(initialValues);
    }, [initialValues]);

    // Group attributes
    const groups = React.useMemo(() => {
        if (!schema?.attributes) return {};
        const g: Record<string, AttributeDefinition[]> = {};

        // Sort by order first
        const sortedAttrs = [...schema.attributes].sort((a, b) => (a.order || 0) - (b.order || 0));

        sortedAttrs.forEach(attr => {
            const groupName = attr.group || '基本信息';
            if (!g[groupName]) g[groupName] = [];
            g[groupName].push(attr);
        });
        return g;
    }, [schema]);

    const groupNames = Object.keys(groups);

    useEffect(() => {
        if (groupNames.length > 0 && !activeGroup) {
            setActiveGroup(groupNames[0]);
        }
    }, [groupNames, activeGroup]);

    const handleChange = (name: string, value: any) => {
        const newValues = { ...values, [name]: value };
        setValues(newValues);
        onChange(newValues);
    };

    if (!schema || !schema.attributes || schema.attributes.length === 0) {
        return (
            <div className="text-center text-sm text-muted-foreground py-4 bg-muted/30 rounded border border-border border-dashed">
                该类型未定义属性
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Tabs */}
            {groupNames.length > 1 && (
                <div className="flex border-b border-border overflow-x-auto">
                    {groupNames.map(group => (
                        <button
                            key={group}
                            onClick={() => setActiveGroup(group)}
                            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${activeGroup === group
                                    ? 'border-primary text-primary'
                                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
                                }`}
                        >
                            {group}
                        </button>
                    ))}
                </div>
            )}

            {/* Content */}
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                {(groups[activeGroup] || []).map((attr) => (
                    <div key={attr.name} className={attr.hidden ? 'hidden' : ''}>
                        <label className="block text-sm font-medium text-foreground mb-1">
                            {attr.label}
                            {attr.required && <span className="text-error ml-0.5">*</span>}
                        </label>
                        {attr.description && (
                            <div className="text-xs text-muted-foreground mb-1.5">{attr.description}</div>
                        )}

                        {renderInput(attr, values[attr.name], (val) => handleChange(attr.name, val), mode)}

                        {/* Validation hints (can be enhanced) */}
                    </div>
                ))}
            </div>
        </div>
    );
}

function renderInput(
    attr: AttributeDefinition,
    value: any,
    onChange: (val: any) => void,
    mode: 'create' | 'edit' | 'view'
) {
    const disabled = mode === 'view' || attr.readonly;
    const placeholder = attr.placeholder || `请输入 ${attr.label}`;

    // Widget: Select / Enum
    if (attr.widget === 'select' || attr.type === 'enum' || (attr.options && attr.options.length > 0)) {
        return (
            <div className="relative">
                <select
                    value={value || ''}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    className="input w-full appearance-none pr-8"
                >
                    <option value="">请选择</option>
                    {attr.options?.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                            {opt.label}
                        </option>
                    ))}
                </select>
                <ChevronDown className="absolute right-3 top-3 h-4 w-4 text-muted-foreground pointer-events-none" />
            </div>
        );
    }

    // Widget: Datepicker (Native for now)
    if (attr.widget === 'datepicker' || attr.type === 'date') {
        return (
            <div className="relative">
                <input
                    type="date"
                    value={value ? String(value).split('T')[0] : ''}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    className="input w-full appearance-none" // pr-10 if adding icon
                />
                {/* <Calendar className="absolute right-3 top-3 h-4 w-4 text-muted-foreground pointer-events-none" /> */}
            </div>
        );
    }

    // Widget: Number
    if (attr.widget === 'number' || attr.type === 'number') {
        return (
            <input
                type="number"
                value={value || ''}
                onChange={(e) => onChange(e.target.value ? parseFloat(e.target.value) : null)}
                disabled={disabled}
                className="input w-full"
                placeholder={placeholder}
                min={attr.min_val}
                max={attr.max_val}
            />
        );
    }

    // Widget: Textarea
    if (attr.widget === 'textarea') {
        return (
            <textarea
                value={value || ''}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                className="input w-full min-h-[80px] py-2"
                placeholder={placeholder}
            />
        );
    }

    // Widget: User Selector (Mock with Icon)
    if (attr.widget === 'user-selector' || attr.type === 'user') {
        return (
            <div className="relative">
                <input
                    type="text"
                    value={value || ''}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    className="input w-full pl-9"
                    placeholder={placeholder || "输入用户名..."}
                />
                <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            </div>
        );
    }

    // Widget: CI Selector (Mock with Icon)
    if (attr.widget === 'ci-selector' || attr.type === 'ci_ref') {
        return (
            <div className="relative">
                <input
                    type="text"
                    value={value || ''}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    className="input w-full pl-9"
                    placeholder={placeholder || "输入CI名称或标识..."}
                />
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            </div>
        );
    }

    // Default: Text Input
    return (
        <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="input w-full"
            placeholder={placeholder}
        />
    );
}
