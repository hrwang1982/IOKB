"use client";

import { useEffect, useState } from "react";
import { AlertCircle, AlertTriangle, CheckCircle, Info, Loader2 } from "lucide-react";
import { getAlerts, type Alert } from "@/lib/api";

const levelConfig: Record<string, { label: string; icon: any; className: string }> = {
    critical: { label: "严重", icon: AlertCircle, className: "text-error bg-error/10" },
    warning: { label: "警告", icon: AlertTriangle, className: "text-warning bg-warning/10" },
    info: { label: "信息", icon: Info, className: "text-info bg-info/10" },
};

const statusConfig: Record<string, { label: string; className: string }> = {
    open: { label: "未处理", className: "bg-error/10 text-error" },
    acknowledged: { label: "已确认", className: "bg-warning/10 text-warning" },
    resolved: { label: "已解决", className: "bg-success/10 text-success" },
};

interface AlertsTableProps {
    ciIdentifier: string;
}

export function AlertsTable({ ciIdentifier }: AlertsTableProps) {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [startTime, setStartTime] = useState<string>("");
    const [endTime, setEndTime] = useState<string>("");
    const [level, setLevel] = useState<string>("");
    const [status, setStatus] = useState<string>("");

    const fetchAlerts = () => {
        if (!ciIdentifier) return;
        setLoading(true);
        getAlerts({
            ci_identifier: ciIdentifier,
            size: 20,
            start_time: startTime ? new Date(startTime).toISOString() : undefined,
            end_time: endTime ? new Date(endTime).toISOString() : undefined,
            level: level || undefined,
            status: status || undefined
        })
            .then((res) => setAlerts(res.items))
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchAlerts();
    }, [ciIdentifier]);

    // Handle manual refresh
    const handleRefresh = () => {
        fetchAlerts();
    };

    // Trigger fetch on filter change ? Or just manual?
    // Let's do manual refresh for inputs to avoid too many requests while typing dates
    // But verify requirement: "执行筛选后对应的查询数据也发生变化" - usually implies click 'search' or auto.
    // Let's add a "Filter" button to be explicit.

    if (loading && alerts.length === 0) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 text-center text-error bg-error/5 rounded-md">
                加载告警失败: {error}
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Filter Toolbar */}
            <div className="flex flex-wrap gap-3 items-end bg-muted/30 p-3 rounded-lg border border-border">
                <div className="grid gap-1">
                    <label className="text-xs font-medium text-muted-foreground">开始时间</label>
                    <input
                        type="datetime-local"
                        className="input h-8 text-sm w-44"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                    />
                </div>
                <div className="grid gap-1">
                    <label className="text-xs font-medium text-muted-foreground">结束时间</label>
                    <input
                        type="datetime-local"
                        className="input h-8 text-sm w-44"
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                    />
                </div>
                <div className="grid gap-1">
                    <label className="text-xs font-medium text-muted-foreground">级别</label>
                    <select
                        className="input h-8 text-sm w-24"
                        value={level}
                        onChange={(e) => setLevel(e.target.value)}
                    >
                        <option value="">全部</option>
                        <option value="critical">严重</option>
                        <option value="warning">警告</option>
                        <option value="info">信息</option>
                    </select>
                </div>
                <div className="grid gap-1">
                    <label className="text-xs font-medium text-muted-foreground">状态</label>
                    <select
                        className="input h-8 text-sm w-24"
                        value={status}
                        onChange={(e) => setStatus(e.target.value)}
                    >
                        <option value="">全部</option>
                        <option value="open">未处理</option>
                        <option value="acknowledged">已确认</option>
                        <option value="resolved">已解决</option>
                    </select>
                </div>
                <button
                    onClick={handleRefresh}
                    className="btn-primary h-8 px-4 flex items-center gap-2"
                >
                    查询
                </button>
            </div>

            {alerts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground border border-dashed border-border rounded-lg">
                    暂无关联告警
                </div>
            ) : (
                <div className="overflow-x-auto border border-border rounded-lg">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-muted-foreground uppercase bg-muted/50">
                            <tr>
                                <th className="px-4 py-3">级别</th>
                                <th className="px-4 py-3">标题</th>
                                <th className="px-4 py-3">状态</th>
                                <th className="px-4 py-3">来源</th>
                                <th className="px-4 py-3">时间</th>
                            </tr>
                        </thead>
                        <tbody>
                            {alerts.map((alert) => {
                                const level = levelConfig[alert.level] || levelConfig.info;
                                const status = statusConfig[alert.status] || statusConfig.open;
                                const LevelIcon = level.icon;

                                return (
                                    <tr key={alert.alert_id} className="border-b border-border hover:bg-muted/30 last:border-0">
                                        <td className="px-4 py-3">
                                            <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${level.className}`}>
                                                <LevelIcon className="h-3 w-3" />
                                                {level.label}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 font-medium text-foreground">
                                            {alert.title}
                                            <div className="text-xs text-muted-foreground mt-0.5 truncate max-w-[300px]">
                                                {alert.content}
                                            </div>
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${status.className}`}>
                                                {status.label}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-muted-foreground">
                                            {alert.source || "Unknown"}
                                        </td>
                                        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                                            {new Date(alert.alert_time).toLocaleString()}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
