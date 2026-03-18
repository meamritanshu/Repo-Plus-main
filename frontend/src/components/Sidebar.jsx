/**
 * Sidebar.jsx — Sleek nested file tree (VS Code style).
 * Shows folders (collapsible) and files with monochrome risk badges.
 */

import { useState } from "react";
import { ActivityIcon, FolderIcon, FileIcon, ChevronRightIcon } from "./icons";
import { getRiskLabel } from "../utils/heatmapUtils";

// Semantic risk badges for developers
const RISK_BADGE = {
    critical: "bg-red-500/20 text-red-500 border border-red-500/30 px-1.5 py-0.5 rounded",
    severe: "bg-orange-500/20 text-orange-400 border border-orange-500/30 px-1.5 py-0.5 rounded",
    moderate: "bg-amber-500/20 text-amber-500 border border-amber-500/30 px-1.5 py-0.5 rounded",
    mild: "bg-emerald-500/10 text-emerald-500/70 border border-emerald-500/20 px-1.5 py-0.5 rounded",
    stable: "opacity-0", // hidden if safe/stable
};

const RISK_ICON_COLOR = {
    critical: "text-red-500",
    severe: "text-orange-500",
    moderate: "text-amber-500",
    mild: "text-emerald-500",
    stable: "text-[#71717a]",
};

function FileItem({ node, selectedFile, onFileSelect, depth }) {
    const risk = node.severity ?? node.risk_score ?? 0;
    const label = getRiskLabel(risk);
    const isSelected = selectedFile === node.path;

    // Calculate precise VS Code style indentation (1rem per depth layer)
    const indentStyles = { paddingLeft: `${depth * 1.2 + 0.5}rem` };

    return (
        <div
            onClick={() => onFileSelect(node.path)}
            style={indentStyles}
            className={`
                flex items-center gap-2 py-1.5 pr-3 cursor-pointer text-[13px] font-mono select-none
                ${isSelected
                    ? "bg-[#27272a] text-white"
                    : "text-[#a1a1aa] hover:bg-[#18181b] hover:text-[#d4d4d8]"
                }
            `}
            title={`${node.path} (${label})`}
        >
            <span className="w-4 h-4 shrink-0 flex items-center justify-center invisible"><ChevronRightIcon size={14} /></span>
            <FileIcon size={14} className={isSelected ? "text-white" : (RISK_ICON_COLOR[label] || "text-[#71717a]")} />
            <span className="truncate flex-1">{node.name}</span>
            <span className={`text-[9px] uppercase tracking-wider shrink-0 transition-opacity ${RISK_BADGE[label] || RISK_BADGE.stable}`}>
                {label === "stable" ? "" : label}
            </span>
        </div>
    );
}

function FolderItem({ node, selectedFile, onFileSelect, depth }) {
    const [open, setOpen] = useState(depth < 1);

    const mapRisk = { critical: 4, severe: 3, moderate: 2, mild: 1, stable: 0 };
    const getNumRisk = (n) => typeof n === 'string' ? mapRisk[n.toLowerCase()] || 0 : n;

    // Folders reflect the maximum risk of their children
    const maxRiskScore = Math.max(0, ...(node.children || []).map(c => getNumRisk(c.severity ?? c.risk_score ?? 0)));
    const label = maxRiskScore >= 4 ? "critical" : maxRiskScore >= 3 ? "severe" : maxRiskScore >= 2 ? "moderate" : maxRiskScore >= 1 ? "mild" : "stable";
    const hasDanger = ["critical", "severe"].includes(label);

    const indentStyles = { paddingLeft: `${depth * 1.2 + 0.5}rem` };

    return (
        <div>
            <div
                onClick={() => setOpen(o => !o)}
                style={indentStyles}
                className="flex items-center gap-2 py-1.5 pr-3 cursor-pointer text-[13px] font-mono text-[#a1a1aa] hover:bg-[#18181b] hover:text-[#e5e5e5] select-none"
            >
                <div className="w-4 h-4 shrink-0 flex items-center justify-center text-[#71717a]">
                    <ChevronRightIcon size={14} expanded={open} />
                </div>
                <FolderIcon size={14} open={open} className={hasDanger ? "text-red-500/80" : "text-[#a1a1aa]"} />
                <span className={`flex-1 truncate ${open ? "font-medium" : ""}`}>{node.name}</span>
                {hasDanger && !open && (
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
                )}
            </div>

            {open && (
                <div className="flex flex-col relative before:absolute before:left-0 before:top-0 before:bottom-0 before:w-px before:bg-[#27272a] before:content-['']">
                    {(node.children || []).map((child, i) =>
                        child.type === "folder" ? (
                            <FolderItem
                                key={`${child.path}-${i}`}
                                node={child}
                                selectedFile={selectedFile}
                                onFileSelect={onFileSelect}
                                depth={depth + 1}
                            />
                        ) : (
                            <FileItem
                                key={`${child.path}-${i}`}
                                node={child}
                                selectedFile={selectedFile}
                                onFileSelect={onFileSelect}
                                depth={depth + 1}
                            />
                        )
                    )}
                </div>
            )}
        </div>
    );
}

export default function Sidebar({ tree, selectedFile, onFileSelect }) {
    const [sortMode, setSortMode] = useState("alpha"); // "alpha" | "risk"
    const [filterMode, setFilterMode] = useState("all"); // "all" | "unstable" | "severe"

    if (!tree) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-[#52525b] text-xs text-center">
                <FolderIcon size={32} className="mb-4 opacity-20" />
                No repository loaded. Enter a URL to begin.
            </div>
        );
    }

    const handleJumpToHottest = () => {
        let hottestFile = null;
        let maxRisk = -1;
        const findHottest = (nodes) => {
            for (const n of nodes) {
                const mapRisk = { critical: 4, severe: 3, moderate: 2, mild: 1, stable: 0 };
                const getNumRisk = (v) => typeof v === 'string' ? mapRisk[v.toLowerCase()] || 0 : v;
                if (n.type === "file") {
                    const r = getNumRisk(n.severity ?? n.risk_score ?? 0);
                    if (r > maxRisk) {
                        maxRisk = r;
                        hottestFile = n.path;
                    }
                } else if (n.type === "folder") {
                    findHottest(n.children || []);
                }
            }
        };
        findHottest(tree.children || []);
        if (hottestFile) {
            onFileSelect(hottestFile);
        }
    };

    const processTree = (nodes) => {
        let result = [];
        const mapRisk = { critical: 4, severe: 3, moderate: 2, mild: 1, stable: 0 };
        for (const node of nodes) {
            if (node.type === "file") {
                const risk = node.severity ?? node.risk_score ?? 0;
                const label = getRiskLabel(risk);
                if (filterMode === "unstable" && label === "stable") continue;
                if (filterMode === "severe" && !["severe", "critical"].includes(label)) continue;
                result.push({ ...node });
            } else if (node.type === "folder") {
                const processedChildren = processTree(node.children || []);
                if (processedChildren.length > 0) {
                    result.push({ ...node, children: processedChildren });
                }
            }
        }

        result.sort((a, b) => {
            if (sortMode === "alpha") {
                if (a.type !== b.type) return a.type === "folder" ? -1 : 1;
                return a.name.localeCompare(b.name);
            } else {
                const riskA = a.type === "folder" ? Math.max(0, ...(a.children || []).map(c => c.risk_score || 0)) : (a.risk_score || 0);
                const riskB = b.type === "folder" ? Math.max(0, ...(b.children || []).map(c => c.risk_score || 0)) : (b.risk_score || 0);
                if (riskA !== riskB) return riskB - riskA;
                return a.name.localeCompare(b.name);
            }
        });

        return result;
    };

    const processedChildren = processTree(tree.children || []);

    return (
        <div className="flex-1 flex flex-col min-h-0">
            {/* Sidebar Tools Header */}
            <div className="p-3 border-b border-[#27272a] bg-[#000000] flex-shrink-0 flex flex-col gap-3">
                <button
                    onClick={handleJumpToHottest}
                    className="w-full bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] text-[#e5e5e5] text-[10px] font-mono uppercase tracking-wider py-1.5 rounded flex items-center justify-center gap-2 transition-colors"
                >
                    <ActivityIcon size={12} className="text-red-500" />
                    Jump to Hottest File
                </button>
                <div className="flex items-center gap-2">
                    <select
                        value={sortMode}
                        onChange={(e) => setSortMode(e.target.value)}
                        className="flex-1 bg-transparent border border-[#27272a] text-[#a1a1aa] text-[10px] uppercase font-mono px-1 py-0.5 rounded outline-none cursor-pointer"
                    >
                        <option value="alpha">Sort: A-Z</option>
                        <option value="risk">Sort: Risk</option>
                    </select>
                    <select
                        value={filterMode}
                        onChange={(e) => setFilterMode(e.target.value)}
                        className="flex-1 bg-transparent border border-[#27272a] text-[#a1a1aa] text-[10px] uppercase font-mono px-1 py-0.5 rounded outline-none cursor-pointer"
                    >
                        <option value="all">View: All</option>
                        <option value="unstable">View: Unstable</option>
                        <option value="severe">View: Severe+</option>
                    </select>
                </div>
            </div>

            {/* Tree */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden pt-2 pb-6">
                {processedChildren.map((node, i) =>
                    node.type === "folder" ? (
                        <FolderItem
                            key={`${node.path}-${i}`}
                            node={node}
                            selectedFile={selectedFile}
                            onFileSelect={onFileSelect}
                            depth={0}
                        />
                    ) : (
                        <FileItem
                            key={`${node.path}-${i}`}
                            node={node}
                            selectedFile={selectedFile}
                            onFileSelect={onFileSelect}
                            depth={0}
                        />
                    )
                )}
                {processedChildren.length === 0 && (
                    <div className="text-center text-[#52525b] text-xs font-mono py-8 px-4">
                        No files match filter criteria.
                    </div>
                )}
            </div>
        </div>
    );
}
