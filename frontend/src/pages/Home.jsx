/**
 * Home.jsx — Landing page with the repository analysis form.
 */

import { useNavigate } from "react-router-dom";
import AnalyzeForm from "../components/AnalyzeForm";
import Loader from "../components/Loader";
import { analyzeRepo } from "../api/repopulse";
import { useState } from "react";

const FEATURES = [
    { icon: "🔍", label: "Commit Mining" },
    { icon: "🔥", label: "Hotspot Detection" },
    { icon: "📊", label: "Churn Analysis" },
    { icon: "⚖️", label: "Risk Scoring" },
    { icon: "🗺️", label: "Dir Heatmap" },
    { icon: "👨‍💻", label: "Dev Insights" },
];

export default function Home() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [repoUrl, setRepoUrl] = useState("");
    const [apiError, setApiError] = useState("");

    const handleSubmit = async ({ repoUrl, maxCommits }) => {
        setRepoUrl(repoUrl);
        setLoading(true);
        setApiError("");
        try {
            const data = await analyzeRepo(repoUrl, maxCommits);
            navigate("/results", { state: { data, repoUrl } });
        } catch (err) {
            const msg = err.response?.data?.error || err.message || "Analysis failed. Please try again.";
            setApiError(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            {loading && <Loader repoUrl={repoUrl} />}
            <section className="hero">
                <div className="hero-content">
                    <div className="hero-badge">
                        <span>🚀</span> GitHub Repository Analyzer
                    </div>

                    <h1 className="hero-title">
                        Find Your Code's{" "}
                        <span className="gradient-text">Hidden Hotspots</span>
                    </h1>

                    <p className="hero-desc">
                        RepoPulse mines commit history, calculates churn and risk scores, and surfaces
                        the files most likely to introduce bugs — all in one beautiful dashboard.
                    </p>

                    <AnalyzeForm onSubmit={handleSubmit} loading={loading} />

                    {apiError && (
                        <div className="error-banner" role="alert" style={{ marginTop: 20 }}>
                            <span>❌</span> {apiError}
                        </div>
                    )}

                    <div className="features-grid" style={{ marginTop: 32 }}>
                        {FEATURES.map(f => (
                            <div key={f.label} className="feature-card">
                                <div className="feature-icon">{f.icon}</div>
                                <div className="feature-label">{f.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>
        </>
    );
}
