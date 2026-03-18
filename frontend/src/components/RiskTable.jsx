/**
 * RiskTable.jsx — Sortable table of file risk scores.
 */

import { useState } from "react";

function getRiskClass(score) {
    if (score >= 0.7) return "high-risk";
    if (score >= 0.4) return "med-risk";
    return "low-risk";
}

function getRankClass(rank) {
    if (rank === 1) return "rank-1";
    if (rank === 2) return "rank-2";
    if (rank === 3) return "rank-3";
    return "rank-n";
}

function getBarColor(score) {
    if (score >= 0.7) return "linear-gradient(90deg, #ff5252, #ff7043)";
    if (score >= 0.4) return "linear-gradient(90deg, #ffca28, #ff9800)";
    return "linear-gradient(90deg, #00c9a7, #00bcd4)";
}

export default function RiskTable({ data }) {
    const [sortKey, setSortKey] = useState("risk_score");
    const [sortDir, setSortDir] = useState("desc");

    if (!data || data.length === 0) return null;

    const handleSort = (key) => {
        if (sortKey === key) {
            setSortDir(d => (d === "asc" ? "desc" : "asc"));
        } else {
            setSortKey(key);
            setSortDir("desc");
        }
    };

    const sorted = [...data].sort((a, b) => {
        const va = a[sortKey] ?? 0;
        const vb = b[sortKey] ?? 0;
        if (typeof va === "string") return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
        return sortDir === "asc" ? va - vb : vb - va;
    });

    const cols = [
        { key: "rank", label: "#" },
        { key: "file_path", label: "File" },
        { key: "commit_frequency", label: "Commits" },
        { key: "total_churn", label: "Churn" },
        { key: "risk_score", label: "Risk Score" },
    ];

    const arrow = (key) => sortKey === key ? (sortDir === "desc" ? " ▾" : " ▴") : "";

    return (
        <div className="table-wrapper">
            <table>
                <thead>
                    <tr>
                        {cols.map(c => (
                            <th key={c.key} onClick={() => handleSort(c.key)}>
                                {c.label}{arrow(c.key)}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {sorted.map((row, i) => (
                        <tr key={`${row.file_path}-${i}`}>
                            <td>
                                <span className={`rank-badge ${getRankClass(row.rank)}`}>{row.rank}</span>
                            </td>
                            <td className="mono" title={row.file_path}>
                                {row.file_path.length > 55 ? "…" + row.file_path.slice(-54) : row.file_path}
                            </td>
                            <td className="mono">{row.commit_frequency}</td>
                            <td className="mono">{row.total_churn?.toLocaleString()}</td>
                            <td>
                                <div className="risk-bar-wrap">
                                    <div className="risk-bar-bg">
                                        <div
                                            className="risk-bar-fill"
                                            style={{
                                                width: `${(row.risk_score * 100).toFixed(1)}%`,
                                                background: getBarColor(row.risk_score),
                                            }}
                                        />
                                    </div>
                                    <span className={`risk-val ${getRiskClass(row.risk_score)}`}>
                                        {row.risk_score.toFixed(3)}
                                    </span>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
