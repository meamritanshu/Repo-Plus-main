/**
 * heatmapUtils.js — Utilities for Monaco heatmap decoration rendering.
 * Pure monochrome aesthetic (greyscale).
 */

/**
 * Convert a normalized intensity (0–1) to an RGBA color string.
 * Semantic overlay for the entire editor line background.
 */
export function intensityToColor(intensity) {
    if (intensity <= 0) return "transparent";
    if (intensity < 0.35) return `rgba(34, 197, 94, ${(0.02 + intensity * 0.1).toFixed(3)})`; // Green
    if (intensity < 0.65) return `rgba(245, 158, 11, ${(0.05 + intensity * 0.15).toFixed(3)})`; // Amber
    return `rgba(239, 68, 68, ${(0.1 + intensity * 0.2).toFixed(3)})`; // Red
}

/**
 * Convert intensity to gutter bar color (brighter semantic color).
 */
export function intensityToGutterColor(intensity) {
    if (intensity <= 0) return "transparent";
    if (intensity < 0.35) return `rgba(34, 197, 94, ${(0.3 + intensity * 0.4).toFixed(3)})`;
    if (intensity < 0.65) return `rgba(245, 158, 11, ${(0.5 + intensity * 0.4).toFixed(3)})`;
    return `rgba(239, 68, 68, ${(0.7 + intensity * 0.3).toFixed(3)})`;
}

/**
 * Build Monaco editor decorations from a heatmap array.
 */
export function buildDecorations(heatmapData, fileMetrics = {}, mode = "intensity", isSmoothed = false) {
    if (!heatmapData || heatmapData.length === 0) return [];

    const getPrefix = (m) => m === "intensity" ? "heat" : m === "volatility" ? "vol" : "rec";

    const getGutterColor = (score, m) => {
        if (score <= 0) return "transparent";
        if (m === "intensity") {
            if (score < 0.35) return `rgba(34, 197, 94, ${(0.3 + score * 0.4).toFixed(3)})`;
            if (score < 0.65) return `rgba(245, 158, 11, ${(0.5 + score * 0.4).toFixed(3)})`;
            return `rgba(239, 68, 68, ${(0.7 + score * 0.3).toFixed(3)})`;
        }
        if (m === "volatility") {
            if (score < 0.35) return `rgba(6, 182, 212, ${(0.3 + score * 0.4).toFixed(3)})`;
            if (score < 0.65) return `rgba(168, 85, 247, ${(0.5 + score * 0.4).toFixed(3)})`;
            return `rgba(236, 72, 153, ${(0.7 + score * 0.3).toFixed(3)})`;
        }
        if (m === "recency") {
            if (score < 0.35) return `rgba(113, 113, 122, ${(0.4 + score * 0.3).toFixed(3)})`;
            if (score < 0.65) return `rgba(147, 197, 253, ${(0.6 + score * 0.4).toFixed(3)})`;
            return `rgba(255, 255, 255, ${(0.8 + score * 0.2).toFixed(3)})`;
        }
        return "transparent";
    };

    const decorations = [];

    for (const entry of heatmapData) {
        if (entry.modification_count === 0) continue;

        let score = 0;
        if (mode === "intensity") {
            score = isSmoothed ? entry.block_intensity : entry.normalized_intensity;
        } else if (mode === "volatility") {
            score = isSmoothed ? entry.block_volatility : entry.line_volatility;
        } else if (mode === "recency") {
            score = isSmoothed ? entry.block_recency : entry.recency_score;
        }

        const prefix = getPrefix(mode);
        const gutterColor = getGutterColor(score, mode);
        const bucket = _intensityBucket(score);

        const topDev = fileMetrics?.top_contributor || "Unknown";
        const lastDate = entry.last_modified_ts ? new Date(entry.last_modified_ts * 1000).toLocaleDateString() : "Unknown";
        const smoothLabel = isSmoothed ? " [Smoothed]" : "";

        let hoverMsg = `**✨ Modified ${entry.modification_count}×**${smoothLabel}\n\n`;
        hoverMsg += `- Mode: ${mode.toUpperCase()} (Score: ${score})\n`;
        hoverMsg += `- Line last edit: ${lastDate}\n`;
        hoverMsg += `- File Top Dev: ${topDev}`;

        decorations.push({
            range: {
                startLineNumber: entry.line_number,
                endLineNumber: entry.line_number,
                startColumn: 1,
                endColumn: 1,
            },
            options: {
                isWholeLine: true,
                className: `${prefix}-line-${bucket}`,
                glyphMarginClassName: `${prefix}-gutter-${bucket}`,
                hoverMessage: { value: hoverMsg },
                overviewRuler: { color: gutterColor, position: 7 },
                minimap: { color: gutterColor, position: 1 },
            },
        });
    }

    return decorations;
}

function _intensityBucket(intensity) {
    if (intensity < 0.35) return "low";
    if (intensity < 0.65) return "med";
    return "high";
}

/**
 * Maps raw risk scores (from old backend) or handles string severity (from new engine).
 */
export function getRiskLabel(scoreOrSeverity) {
    if (typeof scoreOrSeverity === "string") {
        return scoreOrSeverity.toLowerCase();
    }
    const score = Number(scoreOrSeverity) || 0;
    if (score >= 0.8) return "critical";
    if (score >= 0.6) return "severe";
    if (score >= 0.4) return "moderate";
    if (score >= 0.2) return "mild";
    return "stable";
}

export function fmtNum(n) {
    if (!n && n !== 0) return "—";
    return Number(n).toLocaleString();
}
