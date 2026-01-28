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
    const [timeRange, setTimeRange] = useState<string>("24h");
    const [customStart, setCustomStart] = useState<string>("");
    const [customEnd, setCustomEnd] = useState<string>("");

    const ranges = [
        { label: "6H", value: "6h" },
        { label: "24H", value: "24h" },
        { label: "7D", value: "7d" },
        { label: "1M", value: "1m" },
        { label: "自定义", value: "custom" },
    ];

    const fetchData = async () => {
        try {
            setLoading(true);
            setError(null);

            let hours = 12;
            let start_time: string | undefined = undefined;
            let end_time: string | undefined = undefined;
            let window = "5m";

            if (timeRange === "custom") {
                if (!customStart) {
                    // If custom is selected but no date picked, don't fetch or fetch default? 
                    // Let's just return if not ready
                    setLoading(false);
                    return;
                }
                start_time = customStart;
                if (customEnd) {
                    end_time = customEnd;
                }
                // Determine window based on range? 
                // Simple logic: > 7 days -> 1h, > 24h -> 30m, else 5m
                const duration = new Date(end_time || new Date().toISOString()).getTime() - new Date(start_time).getTime();
                const hoursDiff = duration / (1000 * 60 * 60);
                if (hoursDiff > 24 * 7) window = "1h";
                else if (hoursDiff > 24) window = "30m";
            } else {
                switch (timeRange) {
                    case "6h": hours = 6; window = "1m"; break;
                    case "24h": hours = 24; window = "5m"; break;
                    case "7d": hours = 24 * 7; window = "1h"; break;
                    case "1m": hours = 24 * 30; window = "4h"; break;
                    default: hours = 24;
                }
            }

            // If custom range and we have start_time/end_time, pass those
            // Otherwise pass hours
            const params: any = {
                ci_identifier: ciIdentifier,
                metric_name: metricName,
                window: window
            };

            if (timeRange === "custom") {
                params.start_time = start_time;
                params.end_time = end_time;
            } else {
                params.hours = hours;
            }

            const res = await getMetrics(params);
            setData(res.data);
        } catch (err: any) {
            setError(err.message || "加载数据失败");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (ciIdentifier && metricName) {
            if (timeRange !== 'custom' || (customStart)) {
                fetchData();
            }
        }
    }, [ciIdentifier, metricName, timeRange, customStart, customEnd]); // Re-fetch on range change

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
            <div className="flex flex-col md:flex-row justify-between items-center mb-4 gap-4">
                <h3 className="text-sm font-medium text-foreground">
                    {title || metricName} {unit ? `(${unit})` : ''}
                </h3>
                <div className="flex flex-wrap items-center gap-2">
                    <div className="flex bg-muted rounded-md p-0.5">
                        {ranges.map((r) => (
                            <button
                                key={r.value}
                                onClick={() => setTimeRange(r.value)}
                                className={`px-2.5 py-1 text-xs font-medium rounded-sm transition-all ${timeRange === r.value
                                    ? "bg-background text-foreground shadow-sm"
                                    : "text-muted-foreground hover:text-foreground hover:bg-background/50"
                                    }`}
                            >
                                {r.label}
                            </button>
                        ))}
                    </div>
                    {timeRange === 'custom' && (
                        <div className="flex items-center gap-1">
                            <input
                                type="datetime-local"
                                className="input h-7 text-xs w-36 px-1"
                                value={customStart}
                                onChange={e => setCustomStart(e.target.value)}
                            />
                            <span className="text-muted-foreground text-xs">-</span>
                            <input
                                type="datetime-local"
                                className="input h-7 text-xs w-36 px-1"
                                value={customEnd}
                                onChange={e => setCustomEnd(e.target.value)}
                            />
                        </div>
                    )}
                </div>
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
