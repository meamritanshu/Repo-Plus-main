/**
 * AnalyzeForm.jsx — Repository input form with URL validation and depth slider.
 */

import { useState } from "react";

export default function AnalyzeForm({ onSubmit, loading }) {
    const [repoUrl, setRepoUrl] = useState("");
    const [maxCommits, setMaxCommits] = useState(200);
    const [error, setError] = useState("");

    const validate = (url) => {
        if (!url.trim()) return "Please enter a GitHub repository URL.";
        if (!url.startsWith("https://github.com/")) return "URL must start with https://github.com/";
        const parts = url.replace("https://github.com/", "").split("/").filter(Boolean);
        if (parts.length < 2) return "URL must include owner and repository (e.g. https://github.com/owner/repo)";
        return "";
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const err = validate(repoUrl);
        if (err) { setError(err); return; }
        setError("");
        onSubmit({ repoUrl: repoUrl.trim(), maxCommits });
    };

    return (
        <form className="form-card" onSubmit={handleSubmit} noValidate>
            <div>
                <label className="form-label" htmlFor="repo-url">GitHub Repository URL</label>
                <input
                    id="repo-url"
                    type="url"
                    className="form-input"
                    placeholder="https://github.com/facebook/react"
                    value={repoUrl}
                    onChange={(e) => { setRepoUrl(e.target.value); setError(""); }}
                    disabled={loading}
                    autoComplete="off"
                    spellCheck={false}
                />
            </div>

            <div className="form-row">
                <div className="depth-group">
                    <div className="depth-label-row">
                        <label className="form-label" htmlFor="commit-depth" style={{ marginBottom: 0 }}>
                            Commit Depth
                        </label>
                        <span className="depth-value">{maxCommits}</span>
                    </div>
                    <input
                        id="commit-depth"
                        type="range"
                        className="form-range"
                        min={50}
                        max={500}
                        step={50}
                        value={maxCommits}
                        onChange={(e) => setMaxCommits(Number(e.target.value))}
                        disabled={loading}
                    />
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading} id="analyze-btn">
                    {loading ? (
                        <>
                            <span style={{ width: 16, height: 16, border: "2px solid rgba(255,255,255,0.4)", borderTopColor: "white", borderRadius: "50%", display: "inline-block", animation: "spin 0.8s linear infinite" }} />
                            Analyzing…
                        </>
                    ) : (
                        <>🔬 Analyze Repository</>
                    )}
                </button>
            </div>

            {error && (
                <div className="error-banner" role="alert">
                    <span>⚠️</span> {error}
                </div>
            )}
        </form>
    );
}
