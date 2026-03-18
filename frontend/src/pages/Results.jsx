/**
 * Results.jsx — Dashboard page showing analysis results.
 */

import { useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import RiskTable from "../components/RiskTable";
import ChartCard from "../components/ChartCard";
import { chartUrl } from "../api/repopulse";

export default function Results() {
    const location = useLocation();
    const navigate = useNavigate();
    const { data, repoUrl } = location.state || {};

    useEffect(() => {
        if (!data) navigate("/");
    }, [data, navigate]);

    if (!data) return null;

    const charts = data.charts || {};
    const toUrl = (path) => path ? chartUrl(path) : null;

    return (
        <div className="results-page">
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16, marginBottom: 16 }}>
                <div>
                    <h1 className="page-title">📊 Analysis Results</h1>
                    <p className="page-subtitle">Repository code hotspot report</p>
                </div>
                <button className="btn btn-ghost" onClick={() => navigate("/")} id="new-analysis-btn">
                    ← New Analysis
                </button>
            </div>

            {/* Repo Metadata */}
            <div className="repo-meta">
                <div className="meta-chip">
                    🔗 <span><strong>{repoUrl?.replace("https://github.com/", "")}</strong></span>
                </div>
                <div className="meta-chip">
                    📝 Commits Analyzed: <strong>{data.commits_analyzed?.toLocaleString()}</strong>
                </div>
                <div className="meta-chip">
                    📁 Files Tracked: <strong>{data.files_analyzed?.toLocaleString()}</strong>
                </div>
            </div>

            {/* Charts Grid */}
            <div className="section-header">
                <span className="section-icon">📈</span>
                <span className="section-title">Visualizations</span>
            </div>
            <div className="charts-grid">
                <ChartCard title="Top 15 High-Risk Files" src={toUrl(charts.risk_bar)} icon="🔥" />
                <ChartCard title="File Churn Distribution" src={toUrl(charts.churn_dist)} icon="📊" />
                <ChartCard title="Directory Risk Heatmap" src={toUrl(charts.dir_heatmap)} icon="🗺️" />
                <ChartCard title="Developer Contributions" src={toUrl(charts.dev_graph)} icon="👨‍💻" />
            </div>

            {/* Risk Table */}
            <div className="section-header">
                <span className="section-icon">⚠️</span>
                <span className="section-title">File Risk Scores</span>
            </div>
            <RiskTable data={data.risk_scores} />

            {/* Folder Stats */}
            {data.folder_stats?.length > 0 && (
                <>
                    <div className="section-header">
                        <span className="section-icon">🗂️</span>
                        <span className="section-title">Directory Overview</span>
                    </div>
                    <div className="table-wrapper" style={{ marginBottom: 40 }}>
                        <table>
                            <thead>
                                <tr>
                                    <th>Directory</th>
                                    <th>Commits</th>
                                    <th>Files</th>
                                    <th>Total Churn</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.folder_stats.slice(0, 15).map((f, i) => (
                                    <tr key={`${f.folder}-${i}`}>
                                        <td className="mono">{f.folder}</td>
                                        <td className="mono">{f.commit_frequency}</td>
                                        <td className="mono">{f.file_count}</td>
                                        <td className="mono">{f.total_churn?.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            {/* Developer Stats */}
            {data.developer_stats?.length > 0 && (
                <>
                    <div className="section-header">
                        <span className="section-icon">👨‍💻</span>
                        <span className="section-title">Developer Summary</span>
                    </div>
                    <div className="table-wrapper" style={{ marginBottom: 40 }}>
                        <table>
                            <thead>
                                <tr>
                                    <th>Author</th>
                                    <th>Commits</th>
                                    <th>Files Touched</th>
                                    <th>Insertions</th>
                                    <th>Deletions</th>
                                    <th>Total Churn</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.developer_stats.slice(0, 15).map((d, i) => (
                                    <tr key={`${d.author}-${i}`}>
                                        <td>{d.author}</td>
                                        <td className="mono">{d.commit_count}</td>
                                        <td className="mono">{d.files_touched}</td>
                                        <td className="mono" style={{ color: "#00c9a7" }}>{d.total_insertions?.toLocaleString()}</td>
                                        <td className="mono" style={{ color: "#ff7043" }}>{d.total_deletions?.toLocaleString()}</td>
                                        <td className="mono">{d.total_churn?.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
}
