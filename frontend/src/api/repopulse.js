/**
 * repopulse.js — Axios API client for RepoPulse v2 (FastAPI backend on :8000)
 */

import axios from "axios";

const BASE_URL = "http://localhost:8000";

const client = axios.create({
    baseURL: BASE_URL,
    timeout: 600000, // 10 min — large repos can take a while
});

/**
 * Analyze a repository (clone + full analysis + cache).
 */
export async function analyzeRepo(repoUrl, commitDepth = 200) {
    const res = await client.post("/analyze", {
        repo_url: repoUrl,
        commit_depth: commitDepth,
    });
    return res.data;
}

/**
 * Get hierarchical file tree with risk badges.
 */
export async function getRepoTree(repoUrl, window = "all") {
    const res = await client.get("/repo-tree", {
        params: { repo_url: repoUrl, window },
    });
    return res.data;
}

/**
 * Get raw file content.
 */
export async function getFileContent(repoUrl, path) {
    const res = await client.get("/file-content", {
        params: { repo_url: repoUrl, path },
    });
    return res.data.content;
}

/**
 * Get file-level metrics (commits, churn, risk, devs, timeline).
 */
export async function getFileMetrics(repoUrl, path, window = "all") {
    const res = await client.get("/hotspots/file", {
        params: { repo_url: repoUrl, path, window },
    });
    return res.data;
}

/**
 * Get per-line modification heatmap.
 */
export async function getLineHeatmap(repoUrl, path, window = "all") {
    const res = await client.get("/hotspots/line", {
        params: { repo_url: repoUrl, path, window },
    });
    return res.data;
}

/**
 * Health check.
 */
export async function checkHealth() {
    const res = await client.get("/health");
    return res.data;
}

/**
 * Check if the workspace session is still active in the backend memory.
 */
export async function getWorkspaceStatus(repoUrl) {
    const res = await client.get("/workspace-status", {
        params: { repo_url: repoUrl },
    });
    return res.data;
}
