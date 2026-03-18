/**
 * GraphView.jsx — Full-screen interactive force-directed graph.
 * Flattens the nested tree into { nodes, links } for react-force-graph-2d.
 */

import React, { useMemo, useRef, useEffect, useState, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { getRiskLabel } from "../utils/heatmapUtils";
import { LoaderIcon, XCircleIcon } from "./icons";

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Graph Error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="flex-1 flex flex-col items-center justify-center bg-[#000000] text-[#ef4444] text-sm font-mono p-8 text-center">
                    <XCircleIcon size={32} className="mb-4" />
                    <p className="mb-2">The graph engine crashed.</p>
                    <p className="text-[#a1a1aa] text-xs max-w-lg break-words">{this.state.error?.toString()}</p>
                </div>
            );
        }
        return this.props.children;
    }
}

// Map our UI risk strings to HEX colors for the canvas rendering
const RISK_COLORS = {
    critical: "#ef4444", // red-500
    severe: "#f97316", // orange-500
    moderate: "#f59e0b", // amber-500
    mild: "#22c55e", // emerald-500
    stable: "#a1a1aa", // zinc-400 (brighter than 500 so they don't blend into black)
    folder: "#52525b", // zinc-600 (brighter for visibility)
};

/**
 * Recursively flatten the file tree into nodes and links for the force graph.
 */
function buildGraphData(tree) {
    const nodes = [];
    const links = [];

    // Create a fast lookup set to avoid duplicates
    const nodeSet = new Set();

    function traverse(node, parentPath = null) {
        if (!node || nodeSet.has(node.path)) return;
        nodeSet.add(node.path);

        // Create graph node
        const isFolder = node.type === "folder";
        const riskLabel = isFolder ? "folder" : getRiskLabel(node.risk_score || 0);
        const color = RISK_COLORS[riskLabel] || RISK_COLORS.stable;

        // Size nodes: folders slightly larger, files scale with risk
        let val = isFolder ? 12 : 6;
        if (!isFolder && node.risk_score > 0.5) val += 3;

        nodes.push({
            id: node.path,
            name: node.name || node.path,
            type: node.type,
            val,
            color,
            risk_score: node.risk_score,
            churn: node.churn,
        });

        // Create link to parent
        if (parentPath) {
            links.push({
                source: parentPath,
                target: node.path,
                // Make folder-to-folder links slightly stronger/shorter later
            });
        }

        // Recurse
        if (node.children) {
            node.children.forEach(child => traverse(child, node.path));
        }
    }

    // Define an artificial root if none exists to hold everything together
    if (tree && typeof tree === "object") {
        // If tree is already an array of roots, or a single root
        if (Array.isArray(tree.children)) {
            traverse(tree);
        } else {
            // Just in case the data shape is weird, wrap it
            traverse({ path: "root", name: "Repository Base", type: "folder", children: [tree] });
        }
    }

    return { nodes, links };
}

export default function GraphView({ tree, selectedFile, onFileSelect }) {
    const containerRef = useRef(null);
    const graphRef = useRef(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
    const [loading, setLoading] = useState(true);

    // Resize listener
    useEffect(() => {
        const observeTarget = containerRef.current;
        if (!observeTarget) return;

        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                setDimensions({
                    width: entry.contentRect.width,
                    height: entry.contentRect.height
                });
            }
        });

        resizeObserver.observe(observeTarget);
        return () => resizeObserver.unobserve(observeTarget);
    }, []);

    // Compute graph data ONLY when tree changes
    const graphData = useMemo(() => {
        setLoading(true);
        const data = buildGraphData(tree);
        // Slight delay to allow UI to render spinner, graph init can be heavy
        setTimeout(() => setLoading(false), 100);
        return data;
    }, [tree]);

    // Handle node clicks
    const handleNodeClick = useCallback(node => {
        if (node.type !== "folder" && onFileSelect) {
            onFileSelect(node.id);
        }
        // Optionally zoom to node
        if (graphRef.current) {
            graphRef.current.centerAt(node.x, node.y, 600);
            graphRef.current.zoom(4, 600);
        }
    }, [onFileSelect]);

    // Center graph initially
    useEffect(() => {
        if (!loading && graphRef.current) {
            // Wait a tick for physics to settle slightly
            setTimeout(() => {
                if (graphRef.current) {
                    graphRef.current.zoomToFit(400);
                }
            }, 800);
        }
    }, [loading]);

    if (!tree) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center bg-[#000000] text-[#71717a] text-sm font-mono mt-10">
                No repository data available for rendering.
            </div>
        );
    }

    return (
        <div className="flex-1 w-full h-full relative bg-[#000000] overflow-hidden" ref={containerRef}>

            {/* Overlay UI */}
            <div className="absolute top-4 left-4 z-10 flex gap-2">
                <div className="bg-[#18181b]/80 backdrop-blur border border-[#27272a] rounded-md px-3 py-2 text-[10px] font-mono text-[#a1a1aa] shadow-xl">
                    Directory Graph — Scroll to Zoom, Drag to Pan
                </div>
                {loading && (
                    <div className="bg-[#18181b]/80 backdrop-blur border border-[#27272a] rounded-md px-3 py-2 text-[10px] font-mono text-white shadow-xl flex items-center gap-2">
                        <LoaderIcon size={12} /> Rendering Physics...
                    </div>
                )}
            </div>

            <div className="absolute bottom-4 right-4 z-10 flex flex-col gap-1.5 bg-[#18181b]/80 backdrop-blur border border-[#27272a] p-3 rounded-lg text-[10px] font-mono text-[#a1a1aa]">
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Critical Risk File</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span> Severe Risk File</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Moderate Risk File</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Mild Risk File</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#71717a]"></span> Stable File</div>
                <div className="flex items-center gap-2 mt-1 pt-1 border-t border-[#3f3f46]"><span className="w-3 h-3 rounded-full bg-[#27272a] border-2 border-[#4a4a55]"></span> Directory / Folder</div>
            </div>

            {/* Force Graph Canvas */}
            <div className="w-full h-full cursor-grab active:cursor-grabbing">
                <ErrorBoundary>
                    <ForceGraph2D
                        ref={graphRef}
                        width={dimensions.width}
                        height={dimensions.height}
                        graphData={graphData}
                        nodeLabel="name"
                        nodeColor={node => node.id === selectedFile ? "#ffffff" : node.color}
                        nodeRelSize={4}
                        linkColor={() => "#27272a"}
                        linkWidth={1.5}
                        linkDirectionalArrowLength={3.5}
                        linkDirectionalArrowRelPos={1}
                        onNodeClick={handleNodeClick}
                        // Physics tuning for directory structures
                        d3VelocityDecay={0.4}
                        cooldownTicks={150} // Stop calculating layout after 150 ticks to save CPU

                        // Custom canvas rendering for specific shapes (files vs folders)
                        nodeCanvasObject={(node, ctx, globalScale) => {
                            const label = node.name || "root";
                            const size = node.val;

                            ctx.fillStyle = node.id === selectedFile ? "#ffffff" : node.color;
                            ctx.beginPath();

                            // Always draw circles for both files and folders per user request
                            ctx.arc(node.x, node.y, size / 2, 0, 2 * Math.PI, false);
                            ctx.fill();

                            // Folder border
                            if (node.type === "folder") {
                                ctx.strokeStyle = "#4a4a55";
                                ctx.lineWidth = 1.5;
                                ctx.stroke();
                            }

                            const isHovered = false; // We don't have hover state natively without state tracking, but selected acts similarly
                            const isSelected = node.id === selectedFile;
                            const shouldShowText = globalScale >= 2.0 || isSelected;

                            if (shouldShowText) {
                                const baseFontSize = isSelected ? 14 : 10;
                                // Scale font slightly but cap it so it remains readable and proportional to nodes
                                const fontSize = Math.min(baseFontSize / Math.max(globalScale, 0.4), 14);

                                ctx.font = `${fontSize}px JetBrains Mono, monospace`;
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'middle';

                                // Draw text background pill for readability
                                ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
                                const textWidth = ctx.measureText(label).width;
                                const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.5); // some padding

                                const yOffset = size / 2 + fontSize * 0.8; // position text below node

                                ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y + size / 2 + fontSize * 0.1, bckgDimensions[0], bckgDimensions[1]);

                                // Draw text
                                ctx.fillStyle = isSelected ? "#ffffff" : (node.type === "folder" ? "#e5e5e5" : "#a1a1aa");
                                ctx.fillText(label, node.x, node.y + yOffset);
                            }
                        }}
                    />
                </ErrorBoundary>
            </div>
        </div>
    );
}
