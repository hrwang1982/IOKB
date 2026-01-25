import React, { useState, useEffect } from 'react';
import { type AttributeSchema, type AttributeDefinition } from '@/lib/api';

interface DynamicFormProps {
    schema?: AttributeSchema | null;
    initialValues?: Record<string, any>;
    onChange: (values: Record<string, any>) => void;
    mode?: 'create' | 'edit' | 'view';
}

export function DynamicForm({ schema, initialValues = {}, onChange, mode = 'create' }: DynamicFormProps) {
    const [values, setValues] = useState<Record<string, any>>(initialValues);

    useEffect(() => {
        setValues(initialValues);
    }, [initialValues]);

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

    // 按分组渲染？目前 Schema 中没有 groupings，但我们之前计划添加。
    // 这里先简单渲染列表。

    return (
        <div className="space-y-4">
            {schema.attributes.map((attr) => (
                <div key={attr.name}>
                    <label className="block text-sm font-medium text-foreground mb-1">
                        {attr.label} ({attr.name})
                        {attr.required && <span className="text-error ml-0.5">*</span>}
                    </label>
                    <div className="text-xs text-muted-foreground mb-1.5">{attr.description}</div>

                    {renderInput(attr, values[attr.name], (val) => handleChange(attr.name, val), mode)}
                </div>
            ))}
        </div>
    );
}

function renderInput(
    attr: AttributeDefinition,
    value: any,
    onChange: (val: any) => void,
    mode: 'create' | 'edit' | 'view'
) {
    const disabled = mode === 'view';

    if (attr.type === 'boolean') {
        return (
            <div className="flex items-center gap-2">
                <input
                    type="checkbox"
                    checked={!!value}
                    onChange={(e) => onChange(e.target.checked)}
                    disabled={disabled}
                    className="h-4 w-4 rounded border-input bg-background"
                />
                <span className="text-sm">{attr.label}</span>
            </div>
        );
    }

    if (attr.type === 'enum' || (attr.options && attr.options.length > 0)) {
        return (
            <select
                value={value || ''}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                className="input w-full"
            >
                <option value="">请选择</option>
                {attr.options?.map((opt) => (
                    <option key={opt} value={opt}>
                        {opt}
                    </option>
                ))}
            </select>
        );
    }

    if (attr.type === 'number') {
        return (
            <input
                type="number"
                value={value || ''}
                onChange={(e) => onChange(parseFloat(e.target.value))}
                disabled={disabled}
                className="input w-full"
                placeholder={`请输入 ${attr.label}`}
            />
        );
    }

    if (attr.type === 'date') {
        return (
            <input
                type="date"
                value={value || ''}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                className="input w-full"
            />
        );
    }

    // Default to text
    return (
        <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="input w-full"
            placeholder={`请输入 ${attr.label}`}
        />
    );
}
