# 🔬 RepoPulse — GitHub Repository Hotspot Analyzer

> **Find the riskiest files in any GitHub repository — before they bite you.**

RepoPulse mines a repository's commit history and computes file-level risk scores based on modification frequency and code churn. Results are presented in a beautiful React dashboard with interactive charts and tables.

---

## 🏗️ Architecture

```
RepoPulse/
├── backend/               Python + Flask REST API
│   ├── app/
│   │   ├── services/      Core analysis logic
│   │   │   ├── repo_cloner.py        Clone GitHub repos
│   │   │   ├── commit_analyzer.py    Mine commit history (GitPython)
│   │   │   ├── hotspot_calculator.py Compute file/folder/dev metrics
│   │   │   └── risk_engine.py        Normalize & score files
│   │   └── visualization/
│   │       ├── churn_chart.py        Risk bar chart + churn histogram
│   │       ├── heatmap.py            Directory heatmap
│   │       └── developer_graph.py    Developer contribution chart
│   ├── config/settings.py
│   ├── tests/
│   └── run.py
│
└── frontend/              React (Vite) Dashboard
    └── src/
        ├── api/repopulse.js     Axios client
        ├── components/          Loader, ChartCard, RiskTable, AnalyzeForm
        └── pages/               Home.jsx, Results.jsx
```

### Risk Score Formula

```
Risk Score = (commit_frequency_normalized × 0.6) + (total_churn_normalized × 0.4)
```

Both inputs are min-max normalized to `[0, 1]` before weighting.

---

## ⚡ Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 1. Backend Setup

```bash
cd RepoPulse/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py
# Flask API running at http://localhost:5000
```

### 2. Frontend Setup

```bash
cd RepoPulse/frontend
npm install
npm run dev
# React app running at http://localhost:5173
```

---

## 🚀 Usage

1. Open **http://localhost:5173** in your browser
2. Paste a public GitHub repository URL (e.g. `https://github.com/pallets/flask`)
3. Set the commit depth (50–500)
4. Click **Analyze Repository**
5. View your results dashboard:
   - 🔥 Top 15 high-risk files bar chart
   - 📊 File churn distribution
   - 🗺️ Directory risk heatmap
   - 👨‍💻 Developer contributions chart
   - Sortable risk score table
   - Folder-level stats
   - Developer summary table

---

## 🐳 Docker

```bash
cd RepoPulse
docker build -t repopulse-backend .
docker run -p 5000:5000 repopulse-backend
```

---

## 🧪 Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## 📊 Example Output

| Rank | File | Commits | Churn | Risk Score |
|------|------|---------|-------|------------|
| 1 | src/core/parser.py | 142 | 18,430 | 0.982 |
| 2 | src/utils/helpers.py | 98 | 9,210 | 0.741 |
| 3 | README.md | 87 | 5,880 | 0.634 |

---

## 🔮 Future Enhancements

- 🤖 ML-based bug prediction using historical data
- 📑 PDF report export
- 🌿 Branch comparison analysis
- 🔑 GitHub API integration for private repos (OAuth token)
- 📉 Interactive Plotly charts (zoom/pan)
- ⏱️ Time-series churn trends

---

## 📄 License

MIT
