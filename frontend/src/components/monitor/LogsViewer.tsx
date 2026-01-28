"use client";

import { useEffect, useState } from "react";
import { Loader2, Search, RefreshCw, Terminal } from "lucide-react";
import { getLogs, type LogEntry } from "@/lib/api";

interface LogsViewerProps {
    ciIdentifier: string;
}

const levelColors: Record<string, string> = {
    error: "text-red-500",
    critical: "text-red-600 font-bold",
    warning: "text-yellow-500",
    info: "text-blue-500",
    debug: "text-gray-500",
};

export function LogsViewer({ ciIdentifier }: LogsViewerProps) {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [keyword, setKeyword] = useState("");
    const [startTime, setStartTime] = useState<string>("");
    const [endTime, setEndTime] = useState<string>("");

    const fetchLogs = async () => {
        if (!ciIdentifier) return;

        setLoading(true);
        setError(null);
        try {
            const res = await getLogs({
                ci_identifier: ciIdentifier,
                keyword,
                size: 50,
                start_time: startTime ? new Date(startTime).toISOString() : undefined,
                end_time: endTime ? new Date(endTime).toISOString() : undefined
            });
            setLogs(res.items);
        } catch (err: any) {
            setError(err.message || "加载日志失败");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, [ciIdentifier]); // Init load

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        fetchLogs();
    };

    return (
        <div className="space-y-4">
            {/* Toolbar */}
            <div className="flex flex-wrap gap-2 items-center">
                <form onSubmit={handleSearch} className="flex-1 relative min-w-[200px]">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <input
                        className="input w-full pl-9 h-10"
                        placeholder="搜索日志内容..."
                        value={keyword}
                        onChange={(e) => setKeyword(e.target.value)}
                    />
                </form>
                <div className="flex items-center gap-2">
                    <input
                        type="datetime-local"
                        className="input h-10 w-44 text-sm"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                        placeholder="开始时间"
                    />
                    <span className="text-muted-foreground">-</span>
                    <input
                        type="datetime-local"
                        className="input h-10 w-44 text-sm"
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                        placeholder="结束时间"
                    />
                    <button onClick={fetchLogs} className="btn-primary h-10 px-4 flex items-center gap-2">
                        查询
                    </button>
                    <button onClick={() => { setKeyword(""); setStartTime(""); setEndTime(""); fetchLogs(); }} className="btn-outline h-10 px-4" title="重置">
                        <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {/* Logs Console */}
            <div className="bg-black/90 text-gray-300 rounded-lg p-4 font-mono text-xs md:text-sm h-[500px] overflow-y-auto border border-gray-800 shadow-inner">
                {error ? (
                    <div className="text-red-400 text-center py-10">❌ {error}</div>
                ) : logs.length === 0 && !loading ? (
                    <div className="text-gray-500 text-center py-10 flex flex-col items-center gap-2">
                        <Terminal className="h-8 w-8 opacity-50" />
                        <span>暂无日志数据</span>
                    </div>
                ) : (
                    <div className="space-y-1">
                        {logs.map((log, index) => (
                            <div key={index} className="flex gap-3 hover:bg-white/5 p-0.5 rounded -mx-1 px-1">
                                <span className="text-gray-500 shrink-0 select-none w-36">
                                    {new Date(log.timestamp).toLocaleString()}
                                </span>
                                <span className={`uppercase w-16 shrink-0 font-medium ${levelColors[log.log_level.toLowerCase()] || 'text-gray-400'}`}>
                                    [{log.log_level}]
                                </span>
                                <span className="break-all whitespace-pre-wrap">
                                    {log.message}
                                </span>
                            </div>
                        ))}
                        {loading && (
                            <div className="py-2 text-center text-gray-500 animate-pulse">
                                Loading more logs...
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
