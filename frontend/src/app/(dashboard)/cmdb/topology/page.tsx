'use client';

import { useEffect, useState, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Network, Search, Loader2, ZoomIn, ZoomOut, RefreshCw, ChevronLeft } from 'lucide-react';
import { getTopology, type TopologyData } from '@/lib/api';

// 简单节点类型定义
interface GraphNode {
    id: number;
    x: number;
    y: number;
    data: TopologyData['nodes'][0];
    level: number; // 0=center, 1=direct, 2=indirect
}

interface GraphEdge {
    source: GraphNode;
    target: GraphNode;
    type: string;
}

export default function TopologyPage() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const centerId = searchParams.get('ci_id') ? parseInt(searchParams.get('ci_id')!) : undefined;

    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<TopologyData | null>(null);
    const [nodes, setNodes] = useState<GraphNode[]>([]);
    const [edges, setEdges] = useState<GraphEdge[]>([]);
    const [scale, setScale] = useState(1);

    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        loadData();
    }, [centerId]);

    const loadData = async () => {
        setLoading(true);
        try {
            const res = await getTopology(centerId, 2);
            setData(res);
            layoutGraph(res, centerId);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // 简单的同心圆布局算法
    const layoutGraph = (data: TopologyData, centerId?: number) => {
        const width = 800;
        const height = 600;
        const centerX = width / 2;
        const centerY = height / 2;

        const nodeMap = new Map<number, GraphNode>();
        const processedNodes: GraphNode[] = [];

        // 1. 确定中心节点
        let centerNodeData = centerId ? data.nodes.find(n => n.id === centerId) : data.nodes[0];
        if (!centerNodeData && data.nodes.length > 0) centerNodeData = data.nodes[0];

        if (centerNodeData) {
            const centerNode: GraphNode = {
                id: centerNodeData.id,
                x: centerX,
                y: centerY,
                data: centerNodeData,
                level: 0
            };
            nodeMap.set(centerNodeData.id, centerNode);
            processedNodes.push(centerNode);
        }

        // 2. 找出第一层节点 (直接连接中心节点的)
        const centerEdges = data.edges.filter(e => e.source === centerNodeData?.id || e.target === centerNodeData?.id);
        const level1Ids = new Set<number>();
        centerEdges.forEach(e => {
            const otherId = e.source === centerNodeData?.id ? e.target : e.source;
            if (!nodeMap.has(otherId)) level1Ids.add(otherId);
        });

        const level1Count = level1Ids.size;
        const radius1 = 150;
        let i = 0;
        level1Ids.forEach(id => {
            const nodeData = data.nodes.find(n => n.id === id);
            if (nodeData) {
                const angle = (i / level1Count) * 2 * Math.PI;
                const node: GraphNode = {
                    id,
                    x: centerX + Math.cos(angle) * radius1,
                    y: centerY + Math.sin(angle) * radius1,
                    data: nodeData,
                    level: 1
                };
                nodeMap.set(id, node);
                processedNodes.push(node);
                i++;
            }
        });

        // 3. 找出第二层节点 (剩余节点)
        const remainingIds = data.nodes.filter(n => !nodeMap.has(n.id)).map(n => n.id);
        const level2Count = remainingIds.length;
        const radius2 = 300;
        let j = 0;
        remainingIds.forEach(id => {
            const nodeData = data.nodes.find(n => n.id === id);
            if (nodeData) {
                const angle = (j / level2Count) * 2 * Math.PI + (Math.PI / level2Count); // 偏移一点
                const node: GraphNode = {
                    id,
                    x: centerX + Math.cos(angle) * radius2,
                    y: centerY + Math.sin(angle) * radius2,
                    data: nodeData,
                    level: 2
                };
                nodeMap.set(id, node);
                processedNodes.push(node);
                j++;
            }
        });

        setNodes(processedNodes);

        // 构建边
        const graphEdges: GraphEdge[] = [];
        data.edges.forEach(e => {
            const source = nodeMap.get(e.source);
            const target = nodeMap.get(e.target);
            if (source && target) {
                graphEdges.push({ source, target, type: e.type });
            }
        });
        setEdges(graphEdges);
    };

    const handleNodeClick = (node: GraphNode) => {
        router.push(`/cmdb/${node.id}`);
    };

    return (
        <div className="h-[calc(100vh-4rem)] flex flex-col animate-fade-in bg-background">
            {/* 工具栏 */}
            <div className="h-14 border-b border-border flex items-center justify-between px-6">
                <div className="flex items-center gap-4">
                    <button onClick={() => router.back()} className="btn-ghost btn-sm">
                        <ChevronLeft className="h-4 w-4" />
                        返回
                    </button>
                    <h1 className="font-semibold flex items-center gap-2">
                        <Network className="h-5 w-5 text-primary" />
                        配置项拓扑视图
                    </h1>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={() => setScale(s => Math.max(0.5, s - 0.1))} className="btn-outline btn-sm">
                        <ZoomOut className="h-4 w-4" />
                    </button>
                    <span className="text-xs w-12 text-center">{Math.round(scale * 100)}%</span>
                    <button onClick={() => setScale(s => Math.min(2, s + 0.1))} className="btn-outline btn-sm">
                        <ZoomIn className="h-4 w-4" />
                    </button>
                    <div className="w-px h-4 bg-border mx-2"></div>
                    <button onClick={loadData} className="btn-outline btn-sm">
                        <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {/* 画布区域 */}
            <div className="flex-1 overflow-hidden relative bg-muted/5">
                {nodes.length === 0 && !loading && (
                    <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                        暂无拓扑数据
                    </div>
                )}

                <svg
                    ref={svgRef}
                    className="w-full h-full cursor-grab active:cursor-grabbing"
                    viewBox={`0 0 800 600`}
                >
                    <g transform={`translate(0,0) scale(${scale})`} style={{ transformOrigin: '400px 300px' }}>
                        {/* 连线 */}
                        {edges.map((edge, idx) => (
                            <g key={`edge-${idx}`}>
                                <line
                                    x1={edge.source.x}
                                    y1={edge.source.y}
                                    x2={edge.target.x}
                                    y2={edge.target.y}
                                    stroke="hsl(var(--border))"
                                    strokeWidth="1.5"
                                />
                                {/* 简单的箭头或者中间标签可以加在这里，但为了性能先略过 */}
                                <text
                                    x={(edge.source.x + edge.target.x) / 2}
                                    y={(edge.source.y + edge.target.y) / 2}
                                    className="text-[10px] fill-muted-foreground"
                                    textAnchor="middle"
                                    dy="-5"
                                >
                                    {edge.type}
                                </text>
                            </g>
                        ))}

                        {/* 节点 */}
                        {nodes.map(node => (
                            <g
                                key={node.id}
                                transform={`translate(${node.x},${node.y})`}
                                onClick={() => handleNodeClick(node)}
                                className="cursor-pointer transition-transform hover:scale-110"
                            >
                                <circle
                                    r={node.level === 0 ? 30 : 24}
                                    fill={node.level === 0 ? 'hsl(var(--primary))' : 'hsl(var(--card))'}
                                    stroke={node.level === 0 ? 'none' : 'hsl(var(--primary))'}
                                    strokeWidth="2"
                                    className="filter drop-shadow-md"
                                />
                                <text
                                    dy="5"
                                    textAnchor="middle"
                                    fill={node.level === 0 ? 'white' : 'hsl(var(--primary))'}
                                    className="text-xs font-bold pointer-events-none select-none"
                                >
                                    {node.data.type_name?.substring(0, 1) || 'CI'}
                                </text>
                                <text
                                    dy={node.level === 0 ? 45 : 40}
                                    textAnchor="middle"
                                    className="text-xs font-medium fill-foreground pointer-events-none select-none"
                                >
                                    {node.data.name}
                                </text>
                            </g>
                        ))}
                    </g>
                </svg>
            </div>

            {/* 底部图例/信息 */}
            <div className="border-t border-border p-2 bg-background flex justify-between text-xs text-muted-foreground">
                <div>节点数量: {nodes.length} | 关系数量: {edges.length}</div>
                <div>单击节点查看详情</div>
            </div>
        </div>
    );
}
