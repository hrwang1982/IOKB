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

    useEffect(() => {
        if (!ciIdentifier) return;

        setLoading(true);
        getAlerts({ ci_identifier: ciIdentifier, size: 20 })
            .then((res) => setAlerts(res.items))
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    }, [ciIdentifier]);

    if (loading) {
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

    if (alerts.length === 0) {
        return (
            <div className="text-center py-8 text-muted-foreground border border-dashed border-border rounded-lg">
                暂无关联告警
            </div>
        );
    }

    return (
        <div className="overflow-x-auto">
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
                            <tr key={alert.alert_id} className="border-b border-border hover:bg-muted/30">
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
    );
}
