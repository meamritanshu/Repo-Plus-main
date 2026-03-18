/**
 * Loader.jsx — Full-screen loading overlay shown during analysis.
 */

export default function Loader({ repoUrl }) {
    return (
        <div className="loader-overlay" role="status" aria-label="Analyzing repository">
            <div className="loader-ring" />
            <div className="loader-text">
                <strong>🔬 Analyzing Repository</strong>
                {repoUrl && (
                    <span style={{ fontSize: "0.85rem", color: "#6060a0", wordBreak: "break-all", maxWidth: 400 }}>
                        {repoUrl}
                    </span>
                )}
                <span>Mining commits · Computing hotspots · Generating charts…</span>
                <span style={{ fontSize: "0.8rem", marginTop: 6, opacity: 0.6 }}>
                    This may take 30–90 seconds for large repositories.
                </span>
            </div>
        </div>
    );
}
