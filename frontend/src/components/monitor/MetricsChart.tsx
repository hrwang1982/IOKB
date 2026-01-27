"use client";

import { useEffect, useState } from "react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from "recharts";
import { Loader2, RefreshCw } from "lucide-react";
import { getMetrics, type MetricPoint } from "@/lib/api";

interface MetricsChartProps {
    ciIdentifier: string;
    metricName: string;
    title?: string;
    unit?: string;
    color?: string;
    height?: number;
}

export function MetricsChart({
    ciIdentifier,
    metricName,
    title,
    unit = "",
    color = "#3b82f6", // default blue-500
    height = 300
}: MetricsChartProps) {
    const [data, setData] = useState<MetricPoint[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError(null);
            // Default query last 24 hours mostly
            const res = await getMetrics({
                ci_identifier: ciIdentifier,
                metric_name: metricName,
                hours: 12, // Last 12 hours
                window: "5m" // 5 min aggregation
            });
            setData(res.data);
        } catch (err: any) {
            setError(err.message || "加载数据失败");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (ciIdentifier && metricName) {
            fetchData();
        }
    }, [ciIdentifier, metricName]);

    if (loading && data.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center border border-border rounded-lg bg-card" style={{ height }}>
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                <span className="text-sm text-muted-foreground mt-2">加载数据中...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center border border-border rounded-lg bg-card" style={{ height }}>
                <span className="text-sm text-error mb-2">数据加载失败</span>
                <button
                    onClick={fetchData}
                    className="flex items-center gap-1 text-xs text-primary hover:underline"
                >
                    <RefreshCw className="h-3 w-3" /> 重试
                </button>
            </div>
        );
    }

    if (data.length === 0) {
        return (
            <div className="flex items-center justify-center border border-border rounded-lg bg-card text-muted-foreground text-sm" style={{ height }}>
                暂无数据 ({metricName})
            </div>
        );
    }

    // Format Data for Chart
    const chartData = data.map(point => ({
        time: new Date(point.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        fullTime: new Date(point.time).toLocaleString(),
        value: point.value
    }));

    return (
        <div className="w-full bg-card border border-border rounded-lg p-4">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-medium text-foreground">
                    {title || metricName} {unit ? `(${unit})` : ''}
                </h3>
            </div>
            <div style={{ width: '100%', height: height - 60 }}>
                <ResponsiveContainer>
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                        <XAxis
                            dataKey="time"
                            stroke="hsl(var(--muted-foreground))"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            minTickGap={30}
                        />
                        <YAxis
                            stroke="hsl(var(--muted-foreground))"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(value) => `${value}`}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'hsl(var(--popover))',
                                borderColor: 'hsl(var(--border))',
                                borderRadius: '6px',
                                color: 'hsl(var(--popover-foreground))',
                                fontSize: '12px'
                            }}
                            labelStyle={{ color: 'hsl(var(--muted-foreground))', marginBottom: '4px' }}
                            itemStyle={{ color: color }}
                            formatter={(value: any) => [`${Number(value).toFixed(2)} ${unit}`, title || metricName]}
                            labelFormatter={(label, payload) => {
                                if (payload && payload.length > 0) {
                                    return payload[0].payload.fullTime;
                                }
                                return label;
                            }}
                        />
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke={color}
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 4 }}
                            animationDuration={1000}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
