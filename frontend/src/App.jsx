/**
 * App.jsx — RepoPulse v2 Code Heatmap Workspace.
 * Notion/VSCode-style 3-panel IDE: Sidebar | Monaco Editor | Insights Panel
 */

import { useState, useCallback, useRef, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import EditorPanel from "./components/EditorPanel";
import InsightsPanel from "./components/InsightsPanel";
import GraphView from "./components/GraphView";
import { analyzeRepo, getRepoTree, checkHealth, getWorkspaceStatus } from "./api/repopulse";
import { CodeIcon, CheckCircleIcon, XCircleIcon, LoaderIcon, ActivityIcon, FolderIcon } from "./components/icons";

// ── Backend Health Banner ────────────────────────────────────────────────────

function BackendBanner() {
  const [status, setStatus] = useState("checking");

  const ping = async () => {
    try {
      await checkHealth();
      setStatus("online");
    } catch {
      setStatus("offline");
    }
  };

  useEffect(() => {
    ping();
    const id = setInterval(ping, 5000);
    return () => clearInterval(id);
  }, []);

  if (status === "checking") return (
    <div className="flex items-center gap-2 px-3 py-2 mb-6 text-xs text-[#a1a1aa] bg-[#18181b] border border-[#27272a] rounded-md">
      <LoaderIcon size={14} className="opacity-50" />
      <span>Checking backend on port 8000…</span>
    </div>
  );

  if (status === "online") return (
    <div className="flex items-center gap-2 px-3 py-2 mb-6 text-xs text-black bg-white border border-[#e5e5e5] rounded-md font-medium">
      <CheckCircleIcon size={14} />
      <span>Backend online at localhost:8000</span>
    </div>
  );

  return (
    <div className="px-4 py-3 mb-6 bg-[#000000] border border-[#27272a] rounded-md text-xs">
      <div className="flex items-center gap-2 text-[#e5e5e5] mb-3 font-semibold">
        <XCircleIcon size={14} className="text-[#a1a1aa]" />
        Backend not running — launch it first:
      </div>
      <div className="bg-[#18181b] rounded px-3 py-2 font-mono text-[#a1a1aa] select-all break-all border border-[#27272a]">
        python3 ~/Documents/MOGLI/POJECTS/RepoPulse/server.py
      </div>
      <p className="text-[#71717a] mt-3">Open a terminal, paste the command above, hit Enter, then try again.</p>
    </div>
  );
}

// ── Analyze Modal (Notion-style) ─────────────────────────────────────────────

function AnalyzeModal({ onAnalyzed }) {
  const [url, setUrl] = useState("");
  const [depth, setDepth] = useState(150);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState("");
  const [error, setError] = useState("");

  const validate = (u) => {
    if (!u.trim()) return "Enter a GitHub URL.";
    if (!u.startsWith("https://github.com/")) return "Must start with https://github.com/";
    const parts = u.replace("https://github.com/", "").replace(/\.git\/?$/, "").split("/").filter(Boolean);
    if (parts.length < 2) return "Include owner and repo name (e.g. https://github.com/facebook/react)";
    return "";
  };

  const sanitizeUrl = (u) => u.trim().replace(/\.git\/?$/, "").replace(/\/$/, "");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const cleanUrl = sanitizeUrl(url);
    const err = validate(cleanUrl);
    if (err) { setError(err); return; }
    setError("");
    setLoading(true);

    try {
      setStep("Cloning repository…");
      await analyzeRepo(cleanUrl, depth);
      setStep("Building file tree…");
      const tree = await getRepoTree(cleanUrl);
      onAnalyzed({ repoUrl: cleanUrl, tree });
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || "Analysis failed. Is the backend running on port 8000?";
      setError(msg);
      setLoading(false);
      setStep("");
    }
  };

  return (
    <div className="fixed inset-0 bg-[#000000] flex flex-col items-center justify-center z-50 p-6">
      <div className="w-full max-w-[480px]">

        <div className="mb-8 flex flex-col items-center text-center">
          <CodeIcon size={40} className="mb-4 text-white" />
          <h1 className="text-2xl font-semibold tracking-tight text-white mb-1">
            RepoPulse
          </h1>
          <p className="text-[#a1a1aa] text-sm">Code Instability Intelligence Engine</p>
        </div>

        <BackendBanner />

        <form onSubmit={handleSubmit} className="w-full">
          <div className="mb-5">
            <label className="block text-[11px] font-medium text-[#71717a] mb-2 uppercase tracking-wide">
              Repository URL
            </label>
            <input
              id="repo-url"
              type="url"
              value={url}
              onChange={e => { setUrl(e.target.value); setError(""); }}
              placeholder="https://github.com/owner/repository"
              disabled={loading}
              autoComplete="off"
              spellCheck={false}
              className="w-full bg-[#000000] border border-[#27272a] rounded-md px-3 py-2.5 text-sm font-mono text-[#e5e5e5] placeholder-[#3f3f46] outline-none focus:border-[#e5e5e5] transition-colors disabled:opacity-50"
            />
          </div>

          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <label className="text-[11px] font-medium text-[#71717a] uppercase tracking-wide">
                Commit Depth
              </label>
              <span className="text-xs font-mono text-white">{depth}</span>
            </div>
            <input
              type="range"
              min="50"
              max="500"
              step="50"
              value={depth}
              onChange={e => setDepth(Number(e.target.value))}
              disabled={loading}
              className="w-full disabled:opacity-50"
            />
            <div className="flex justify-between text-[10px] text-[#52525b] mt-2 font-mono">
              <span>50</span>
              <span>500</span>
            </div>
          </div>

          {error && (
            <div className="mb-6 p-3 bg-[#0a0a0a] border border-[#27272a] rounded-md text-[#e5e5e5] text-xs flex items-start gap-2">
              <XCircleIcon size={14} className="mt-0.5 shrink-0 text-[#a1a1aa]" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white hover:bg-[#e5e5e5] text-black font-medium py-2.5 rounded-md text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <LoaderIcon size={14} className="text-[#71717a]" />
                <span className="text-[#71717a]">{step}</span>
              </>
            ) : "Analyze Workspace"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ── Application Shell ────────────────────────────────────────────────────────

export default function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [tree, setTree] = useState(null);
  const [openFiles, setOpenFiles] = useState([]);
  const [activeFile, setActiveFile] = useState(null);
  const [viewMode, setViewMode] = useState("explorer"); // "explorer" | "visualize"
  const [timeWindow, setTimeWindow] = useState("all");
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    if (!repoUrl) {
      setIsExpired(false);
      return;
    }

    const checkStatus = () => {
      getWorkspaceStatus(repoUrl).then(status => {
        if (!status.active) setIsExpired(true);
      }).catch(() => setIsExpired(true));
    };

    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, [repoUrl]);

  useEffect(() => {
    if (!repoUrl || isExpired) return;
    getRepoTree(repoUrl, timeWindow)
      .then(newTree => setTree(newTree))
      .catch(console.error);
  }, [timeWindow, repoUrl, isExpired]);

  const handleFileSelect = (filePath) => {
    if (!openFiles.includes(filePath)) {
      setOpenFiles([...openFiles, filePath]);
    }
    setActiveFile(filePath);
  };

  const handleFileClose = (filePath) => {
    const newOpenFiles = openFiles.filter(f => f !== filePath);
    setOpenFiles(newOpenFiles);
    if (activeFile === filePath) {
      setActiveFile(newOpenFiles.length > 0 ? newOpenFiles[newOpenFiles.length - 1] : null);
    }
  };

  const handleAnalyzed = ({ repoUrl, tree }) => {
    setRepoUrl(repoUrl);
    setTree(tree);
  };

  const handleReset = () => {
    setRepoUrl("");
    setTree(null);
    setOpenFiles([]);
    setActiveFile(null);
    setViewMode("explorer");
    setTimeWindow("all");
    setIsExpired(false);
  };

  return (
    <div className="h-screen w-full flex flex-col bg-[#000000] text-[#e5e5e5] overflow-hidden selection:bg-white/20">
      {/* Top Navbar */}
      <header className="h-10 border-b border-[#27272a] bg-[#000000] flex items-center px-4 justify-between select-none">
        <div className="flex items-center gap-3">
          <CodeIcon size={16} className="text-[#a1a1aa]" />
          <h1 className="text-xs font-semibold tracking-wide text-[#e5e5e5]">RepoPulse <span className="text-[#52525b] ml-1 font-normal">v2</span></h1>
        </div>

        {repoUrl && (
          <div className="flex items-center gap-4">
            <select
              value={timeWindow}
              onChange={e => setTimeWindow(e.target.value)}
              className="text-[10px] uppercase font-mono bg-[#18181b] border border-[#27272a] text-[#a1a1aa] px-2 py-1 flex-shrink-0 cursor-pointer rounded outline-none hover:text-[#e5e5e5]"
            >
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="6m">Last 6 Months</option>
              <option value="all">All Time</option>
            </select>
            <div className="text-[10px] font-mono text-[#a1a1aa] flex-shrink-0 bg-[#18181b] px-2 py-1 rounded border border-[#27272a]">
              {repoUrl.replace("https://github.com/", "")}
            </div>
            <button
              onClick={handleReset}
              className="text-[10px] uppercase font-medium text-[#71717a] hover:text-[#e5e5e5] transition-colors"
            >
              Close Workspace
            </button>
          </div>
        )}
      </header>

      {/* Main Workspace */}
      <div className="flex-1 flex overflow-hidden relative">

        {isExpired && repoUrl && (
          <div className="absolute inset-0 z-50 bg-[#000000]/90 backdrop-blur-sm flex flex-col items-center justify-center">
            <div className="bg-[#0a0a0a] border border-[#27272a] p-8 rounded-lg flex flex-col items-center max-w-md text-center shadow-2xl">
              <XCircleIcon size={32} className="text-red-500 mb-4" />
              <h2 className="text-white text-lg font-medium mb-2">Workspace Session Expired</h2>
              <p className="text-[#a1a1aa] text-sm mb-6">
                The repository analyzing cache lasts for 1 hour. This session has expired or the backend server restarted.
              </p>
              <button
                onClick={handleReset}
                className="bg-white text-black px-6 py-2 rounded-md font-medium text-sm hover:bg-[#e5e5e5] transition-colors"
              >
                Reload Workspace
              </button>
            </div>
          </div>
        )}

        {viewMode === "explorer" ? (
          <>
            {/* Left Sidebar: File Tree */}
            <div className="w-64 flex-shrink-0 border-r border-[#27272a] bg-[#000000] flex flex-col">
              <div className="px-4 py-2 border-b border-[#27272a] flex items-center justify-between flex-shrink-0">
                <div className="flex items-center gap-1 bg-[#18181b] p-0.5 rounded border border-[#27272a]">
                  <button onClick={() => setViewMode("explorer")} className="px-2 py-1 bg-[#27272a] text-white rounded-[2px] text-[9px] font-medium uppercase tracking-wider">Explorer</button>
                  <button onClick={() => setViewMode("visualize")} className="px-2 py-1 text-[#71717a] hover:text-[#e5e5e5] transition-colors rounded-[2px] text-[9px] font-medium uppercase tracking-wider">Visualize</button>
                </div>
              </div>
              <Sidebar
                tree={tree}
                selectedFile={activeFile}
                onFileSelect={handleFileSelect}
              />
            </div>

            {/* Center: Monaco Editor */}
            <EditorPanel
              repoUrl={repoUrl}
              activeFile={activeFile}
              openFiles={openFiles}
              onFileSelect={setActiveFile}
              onFileClose={handleFileClose}
              timeWindow={timeWindow}
            />

            {/* Right Sidebar: Contextual Insights */}
            <InsightsPanel
              repoUrl={repoUrl}
              selectedFile={activeFile}
              timeWindow={timeWindow}
            />
          </>
        ) : (
          <>
            {/* Left Sidebar showing just graph controls when in visualize mode */}
            <div className="w-64 flex-shrink-0 border-r border-[#27272a] bg-[#000000] flex flex-col">
              <div className="px-4 py-2 border-b border-[#27272a] flex items-center justify-between flex-shrink-0">
                <div className="flex items-center gap-1 bg-[#18181b] p-0.5 rounded border border-[#27272a]">
                  <button onClick={() => setViewMode("explorer")} className="px-2 py-1 text-[#71717a] hover:text-[#e5e5e5] transition-colors rounded-[2px] text-[9px] font-medium uppercase tracking-wider">Explorer</button>
                  <button onClick={() => setViewMode("visualize")} className="px-2 py-1 bg-[#27272a] text-white rounded-[2px] text-[9px] font-medium uppercase tracking-wider">Visualize</button>
                </div>
              </div>
              <div className="p-4 flex flex-col items-center justify-center h-full text-[#71717a] text-xs text-center border-t border-[#18181b] gap-4">
                <ActivityIcon size={32} className="opacity-30" />
                <div>Interactive 2D node-link graph mapping the active repository tree.</div>
                <div className="text-[10px] bg-[#18181b] p-2 rounded border border-[#27272a] w-full mt-4 flex flex-col gap-1 items-start text-left font-mono">
                  <div><span className="text-white">-</span> Scroll to zoom</div>
                  <div><span className="text-white">-</span> Drag to pan</div>
                  <div><span className="text-white">-</span> Click node to open</div>
                </div>
              </div>
            </div>

            <GraphView
              tree={tree}
              selectedFile={activeFile}
              onFileSelect={(file) => {
                handleFileSelect(file);
                setViewMode("explorer"); // switch back to editor to view code
              }}
            />
          </>
        )}
      </div>

      {!repoUrl && <AnalyzeModal onAnalyzed={handleAnalyzed} />}
    </div>
  );
}
