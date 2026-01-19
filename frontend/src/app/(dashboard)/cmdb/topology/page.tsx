'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
    ArrowLeft,
    ChevronRight,
    Database,
    Maximize2,
    Minimize2,
    Network,
    Server,
    ZoomIn,
    ZoomOut,
} from 'lucide-react';

export default function TopologyPage() {
    const [zoom, setZoom] = useState(100);
    const [fullscreen, setFullscreen] = useState(false);

    return (
        <div className={`space-y-6 animate-fade-in ${fullscreen ? 'fixed inset-0 z-50 bg-background p-6' : ''}`}>
            {/* 面包屑 */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Link href="/cmdb" className="hover:text-primary flex items-center gap-1">
                        <ArrowLeft className="h-4 w-4" />
                        配置项列表
                    </Link>
                    <ChevronRight className="h-4 w-4" />
                    <span className="text-foreground">拓扑图</span>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setZoom(Math.max(50, zoom - 10))}
                        className="btn-ghost p-2"
                    >
                        <ZoomOut className="h-4 w-4" />
                    </button>
                    <span className="text-sm text-muted-foreground min-w-[60px] text-center">
                        {zoom}%
                    </span>
                    <button
                        onClick={() => setZoom(Math.min(200, zoom + 10))}
                        className="btn-ghost p-2"
                    >
                        <ZoomIn className="h-4 w-4" />
                    </button>
                    <button
                        onClick={() => setFullscreen(!fullscreen)}
                        className="btn-ghost p-2"
                    >
                        {fullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                    </button>
                </div>
            </div>

            {/* 拓扑图画布 */}
            <div className="card p-6 h-[calc(100vh-12rem)] overflow-hidden">
                <div className="h-full bg-muted/20 rounded-lg flex items-center justify-center relative">
                    {/* 简化的拓扑图示意 */}
                    <div
                        className="space-y-8"
                        style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'center' }}
                    >
                        {/* 网络层 */}
                        <div className="flex justify-center">
                            <div className="card p-4 w-48 text-center hover:border-primary/50 transition-colors cursor-pointer">
                                <Network className="h-8 w-8 mx-auto text-primary mb-2" />
                                <div className="font-medium text-foreground">router-core-001</div>
                                <div className="text-sm text-muted-foreground">网络设备</div>
                            </div>
                        </div>

                        {/* 连接线 */}
                        <div className="flex justify-center">
                            <div className="w-0.5 h-16 bg-border" />
                        </div>

                        {/* 服务器层 */}
                        <div className="flex gap-8 justify-center">
                            {[
                                { name: 'server-prod-001', type: '物理服务器' },
                                { name: 'server-prod-002', type: '物理服务器' },
                                { name: 'server-prod-003', type: '物理服务器' },
                            ].map((server, idx) => (
                                <div key={idx} className="flex flex-col items-center">
                                    <Link
                                        href={`/cmdb/${idx + 1}`}
                                        className="card p-4 w-44 text-center hover:border-primary/50 transition-colors cursor-pointer"
                                    >
                                        <Server className="h-8 w-8 mx-auto text-accent mb-2" />
                                        <div className="font-medium text-foreground">{server.name}</div>
                                        <div className="text-sm text-muted-foreground">{server.type}</div>
                                    </Link>
                                    <div className="w-0.5 h-12 bg-border mt-4" />
                                </div>
                            ))}
                        </div>

                        {/* 应用层 */}
                        <div className="flex gap-8 justify-center">
                            {[
                                { name: 'app-web-001', type: '应用服务' },
                                { name: 'db-master-001', type: '数据库' },
                                { name: 'app-api-001', type: '应用服务' },
                            ].map((app, idx) => (
                                <Link
                                    key={idx}
                                    href={`/cmdb/${idx + 10}`}
                                    className="card p-4 w-44 text-center hover:border-primary/50 transition-colors cursor-pointer"
                                >
                                    <Database className="h-8 w-8 mx-auto text-success mb-2" />
                                    <div className="font-medium text-foreground">{app.name}</div>
                                    <div className="text-sm text-muted-foreground">{app.type}</div>
                                </Link>
                            ))}
                        </div>
                    </div>

                    {/* 图例 */}
                    <div className="absolute bottom-4 right-4 card p-4 space-y-2">
                        <div className="text-sm font-medium text-foreground mb-2">图例</div>
                        <div className="flex items-center gap-2 text-sm">
                            <Network className="h-4 w-4 text-primary" />
                            <span className="text-muted-foreground">网络设备</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                            <Server className="h-4 w-4 text-accent" />
                            <span className="text-muted-foreground">物理服务器</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                            <Database className="h-4 w-4 text-success" />
                            <span className="text-muted-foreground">应用/数据库</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* 提示信息 */}
            <div className="card p-4 bg-primary/5 border-primary/20">
                <p className="text-sm text-muted-foreground text-center">
                    💡 提示: 点击配置项可查看详情，拖拽可移动视图，滚轮可缩放
                </p>
            </div>
        </div>
    );
}
