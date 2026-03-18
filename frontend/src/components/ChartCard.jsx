/**
 * ChartCard.jsx — Card wrapper for a generated analysis chart image.
 */

export default function ChartCard({ title, src, icon }) {
    if (!src) return null;

    return (
        <div className="chart-card">
            <div className="section-header" style={{ marginBottom: 12 }}>
                {icon && <span className="section-icon">{icon}</span>}
                <span className="chart-card-title">{title}</span>
            </div>
            <img
                src={src}
                alt={title}
                loading="lazy"
                onError={(e) => { e.target.style.display = "none"; }}
            />
        </div>
    );
}
