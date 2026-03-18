/**
 * InsightsPanel.jsx — Context-aware analytics panel for the selected file.
 * Classy monochrome aesthetic: pure blacks, whites, and greys.
 */

import { useEffect, useState } from "react";
import { getFileMetrics } from "../api/repopulse";
import { fmtNum, getRiskLabel } from "../utils/heatmapUtils";
import { ActivityIcon, UserIcon, ClockIcon } from "./icons";

// ── Sub-components ────────────────────────────────────────────────────────────

function RiskGauge({ score }) {
    const validScore = typeof score === 'number' && !isNaN(score) ? score : 0;
    const pct = Math.round(validScore * 100);
    const label = getRiskLabel(validScore);

    // Semantic colors for developer understanding
    const colors = {
        critical: "#ef4444", // Red
        severe: "#f97316", // Orange
        moderate: "#f59e0b", // Amber
        mild: "#22c55e", // Emerald
        stable: "#71717a"  // Grey
    };
    const color = colors[label] || "#71717a";

    const stroke = 2 * Math.PI * 36; // circumference of r=36

    return (
        <div className="flex flex-col items-center gap-3">
            <div
                className="relative w-28 h-28 cursor-help"
                title="Volatility (0-100) measures how quickly and recently this file changes. Recent heavy edits = High, spread-out steady edits = Low."
            >
                <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
                    <circle cx="40" cy="40" r="36" fill="none" stroke="#27272a" strokeWidth="3" />
                    <circle
                        cx="40" cy="40" r="36" fill="none"
                        stroke={color} strokeWidth="3"
                        strokeDasharray={stroke}
                        strokeDashoffset={stroke * (1 - validScore)}
                        strokeLinecap="round"
                        style={{ transition: "stroke-dashoffset 0.6s ease, stroke 0.3s" }}
                    />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-semibold font-mono" style={{ color }}>{pct}</span>
                    <span className="text-[9px] uppercase tracking-widest text-[#a1a1aa] mt-0.5 border-b border-dashed border-[#52525b]">volatility</span>
                </div>
            </div>
            <span className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 border rounded ${label === "critical" ? "bg-red-500/10 text-red-500 border-red-500/30 font-bold" :
                label === "severe" ? "bg-orange-500/10 text-orange-400 border-orange-500/30" :
                    label === "moderate" ? "bg-amber-500/10 text-amber-500 border-amber-500/30" :
                        label === "mild" ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30" :
                            "bg-transparent text-[#71717a] border-[#27272a]"
                }`}>
                {label} severity
            </span>
        </div>
    );
}

function StatBlock({ label, value, sub }) {
    return (
        <div className="bg-[#000000] border border-[#27272a] rounded-lg p-3 flex flex-col gap-1.5 h-full">
            <span className="text-[9px] text-[#71717a] uppercase tracking-widest">{label}</span>
            <span className="text-xl font-medium font-mono text-white tracking-tight">{value}</span>
            {sub && <span className="text-[10px] text-[#52525b] font-mono">{sub}</span>}
        </div>
    );
}

function DevBar({ devStats, themeColor = "#ffffff" }) {
    if (!devStats?.length) return null;
    const max = Math.max(...devStats.map(d => d.commit_count), 1);
    return (
        <div className="space-y-3">
            {devStats.slice(0, 6).map((dev, i) => {
                const pct = (dev.commit_count / max) * 100;
                return (
                    <div key={`${dev.author}-${i}`} className="flex items-center gap-3">
                        <span className="text-[10px] text-[#a1a1aa] w-24 truncate shrink-0" title={dev.author}>
                            {dev.author}
                        </span>
                        <div className="flex-1 h-1 bg-[#27272a] rounded-full overflow-hidden">
                            <div
                                className="h-full transition-all duration-500 rounded-full w-0"
                                style={{ width: `${pct}%`, backgroundColor: themeColor }}
                            />
                        </div>
                        <span className="text-[10px] font-mono text-[#52525b] w-6 text-right shrink-0">
                            {dev.commit_count}
                        </span>
                    </div>
                );
            })}
        </div>
    );
}

function Sparkline({ timeline, themeColor = "#ffffff" }) {
    if (!timeline?.length) return null;
    const values = timeline.map(t => t.churn);
    const max = Math.max(...values, 1);
    const W = 220, H = 40;
    const pts = values.map((v, i) => {
        const x = (i / Math.max(values.length - 1, 1)) * W;
        const y = H - (v / max) * H;
        return `${x},${y}`;
    }).join(" ");

    return (
        <div className="mt-2">
            <div className="text-[9px] text-[#71717a] uppercase tracking-widest mb-3 flex items-center justify-between">
                <span>Churn Timeline</span>
                <span>{timeline.length} months</span>
            </div>
            <svg width={W} height={H + 4} className="overflow-visible">
                <polyline
                    points={pts}
                    fill="none"
                    stroke={themeColor}
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
                {values.map((v, i) => {
                    const x = (i / Math.max(values.length - 1, 1)) * W;
                    const y = H - (v / max) * H;
                    return <circle key={i} cx={x} cy={y} r="2.5" fill="#000000" stroke={themeColor} strokeWidth="1" />;
                })}
            </svg>
        </div>
    );
}

function CommitList({ timeline }) {
    if (!timeline?.length) return null;
    const recent = [...timeline].reverse().slice(0, 5);
    return (
        <div className="space-y-2.5">
            {recent.map((entry, i) => (
                <div key={`${entry.date}-${i}`} className="flex flex-col gap-0.5">
                    <div className="flex items-center justify-between text-xs text-[#d4d4d8]">
                        <span>{entry.commits} commit{entry.commits !== 1 ? "s" : ""}</span>
                        <span className="font-mono text-[#52525b] text-[10px]">{fmtNum(entry.churn)} churn</span>
                    </div>
                    <span className="font-mono text-[9px] text-[#71717a] uppercase">{entry.date}</span>
                </div>
            ))}
        </div>
    );
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function InsightsPanel({ repoUrl, selectedFile }) {
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!selectedFile || !repoUrl) {
            setMetrics(null);
            return;
        }
        setLoading(true);
        setError(null);
        getFileMetrics(repoUrl, selectedFile)
            .then(data => {
                setMetrics(data);
                setLoading(false);
            })
            .catch(err => {
                setError(err.message || "Failed to load metrics");
                setLoading(false);
            });
    }, [selectedFile, repoUrl]);

    // ── Empty state ──────────────────────────────────────────────────────────
    if (!selectedFile) {
        return (
            <div className="w-72 flex-shrink-0 flex flex-col items-center justify-center bg-[#000000] border-l border-[#27272a] text-center p-6 gap-4">
                <ActivityIcon size={32} className="text-[#27272a]" />
                <p className="text-[#71717a] text-xs font-mono uppercase tracking-widest">Awaiting Selection</p>
                <p className="text-[#52525b] text-[10px] max-w-[180px]">Select a file to inspect its historical context.</p>
            </div>
        );
    }

    const currentRiskLabel = metrics ? getRiskLabel(metrics.severity ?? metrics.volatility ?? 0) : "stable";
    const RISK_COLORS = { critical: "#ef4444", severe: "#f97316", moderate: "#f59e0b", mild: "#22c55e", stable: "#71717a" };
    const themeColor = RISK_COLORS[currentRiskLabel] || "#71717a";

    return (
        <div className="w-72 flex-shrink-0 flex flex-col bg-[#000000] border-l border-[#27272a] overflow-y-auto">
            {/* Header */}
            <div className="px-5 py-4 border-b border-[#27272a] flex-shrink-0">
                <div className="flex items-center gap-2 mb-1 text-white">
                    <ActivityIcon size={14} className="text-[#a1a1aa]" />
                    <span className="text-xs font-medium tracking-wide">Insights</span>
                </div>
                <div className="text-[10px] font-mono text-[#71717a] truncate mt-1" title={selectedFile}>
                    {selectedFile.split("/").pop()}
                </div>
            </div>

            {loading && (
                <div className="flex-1 flex items-center justify-center">
                    <div className="w-4 h-4 border-2 border-transparent border-t-white rounded-full animate-spin" />
                </div>
            )}

            {error && (
                <div className="m-5 p-4 bg-[#0a0a0a] border border-[#27272a] rounded-lg text-[#e5e5e5] text-xs font-mono">
                    Failed to fetch: {error}
                </div>
            )}

            {metrics && !loading && (
                <div className="flex-1 p-5 space-y-8 overflow-y-auto">
                    {/* Risk Gauge */}
                    <div className="flex justify-center border-b border-[#27272a] pb-8">
                        <RiskGauge score={metrics.volatility ?? 0} />
                    </div>

                    {/* Key numbers */}
                    <div className="grid grid-cols-2 gap-3">
                        <StatBlock
                            label="Commits"
                            value={fmtNum(metrics.commit_count)}
                        />
                        <StatBlock
                            label="Churn"
                            value={fmtNum(metrics.total_churn || metrics.churn)}
                            sub={`+${fmtNum(metrics.insertions)} / -${fmtNum(metrics.deletions)}`}
                        />
                    </div>

                    {/* Top contributor */}
                    {metrics.top_contributor && (
                        <div className="bg-[#000000] border border-[#27272a] rounded-lg p-4">
                            <div className="text-[9px] text-[#71717a] uppercase tracking-widest mb-2 flex items-center gap-1.5">
                                <UserIcon size={10} /> Dominant Author
                            </div>
                            <div className="text-xs font-medium text-white truncate px-1">
                                {metrics.top_contributor}
                            </div>
                            {metrics.last_commit_date && (
                                <div className="text-[10px] text-[#a1a1aa] mt-2 font-mono flex items-center gap-1.5 bg-[#18181b] px-2 py-1.5 rounded">
                                    <ClockIcon size={10} />
                                    {metrics.last_commit_date}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Developer distribution */}
                    {metrics.devStats?.length > 0 && (
                        <div>
                            <div className="text-[9px] text-[#71717a] uppercase tracking-widest mb-4">
                                Contributor Spread
                            </div>
                            <DevBar devStats={metrics.devStats} themeColor={themeColor} />
                        </div>
                    )}

                    {/* Sparkline */}
                    {metrics.timeline?.length > 1 && (
                        <div className="border-t border-[#27272a] pt-6">
                            <Sparkline timeline={metrics.timeline} themeColor={themeColor} />
                        </div>
                    )}

                    {/* Recent activity */}
                    {metrics.timeline?.length > 0 && (
                        <div className="border-t border-[#27272a] pt-6">
                            <div className="text-[9px] text-[#71717a] uppercase tracking-widest mb-4">
                                Historical Windows
                            </div>
                            <CommitList timeline={metrics.timeline} />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
