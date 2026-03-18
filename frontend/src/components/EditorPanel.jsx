/**
 * EditorPanel.jsx — Monaco Editor with live heatmap decoration overlay.
 * Classy monochrome aesthetic: pure blacks, whites, and greys.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import Editor from "@monaco-editor/react";
import { getFileContent, getLineHeatmap, getFileMetrics } from "../api/repopulse";
import { buildDecorations } from "../utils/heatmapUtils";
import { FileIcon, LoaderIcon, CodeIcon, XIcon, ChevronRightIcon, CheckCircleIcon } from "./icons";

const EDITOR_OPTIONS = {
    readOnly: true,
    minimap: { enabled: true },
    scrollBeyondLastLine: false,
    fontSize: 13,
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    lineNumbers: "on",
    glyphMargin: true,
    folding: true,
    renderLineHighlight: "none",
    renderWhitespace: "none",
    smoothScrolling: true,
    cursorStyle: "line",
    wordWrap: "off",
    overviewRulerBorder: false,
};

function detectLanguage(path) {
    if (!path) return "plaintext";
    const ext = path.split(".").pop()?.toLowerCase();
    const map = {
        py: "python", js: "javascript", jsx: "javascript",
        ts: "typescript", tsx: "typescript", css: "css",
        html: "html", json: "json", md: "markdown",
        yaml: "yaml", yml: "yaml", sh: "shell", bash: "shell",
        go: "go", rs: "rust", java: "java", cpp: "cpp", c: "c",
        rb: "ruby", php: "php", toml: "ini", txt: "plaintext",
    };
    return map[ext] || "plaintext";
}

function LoadingOverlay({ message }) {
    return (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#000000]/80 z-10 gap-3 backdrop-blur-sm">
            <LoaderIcon size={24} className="text-[#a1a1aa]" />
            <span className="text-[#a1a1aa] text-xs font-mono tracking-widest uppercase">{message}</span>
        </div>
    );
}

export default function EditorPanel({ repoUrl, activeFile, openFiles, onFileSelect, onFileClose, timeWindow }) {
    const editorRef = useRef(null);
    const monacoRef = useRef(null);
    const decorationsRef = useRef([]);

    const [content, setContent] = useState("");
    const [loadingContent, setLoadingContent] = useState(false);
    const [loadingHeat, setLoadingHeat] = useState(false);
    const [error, setError] = useState(null);
    const [heatStats, setHeatStats] = useState(null); // { maxCount, hotLines }
    const [heatmapMode, setHeatmapMode] = useState("intensity");
    const [isSmoothed, setIsSmoothed] = useState(false);

    useEffect(() => {
        if (!activeFile || !repoUrl) return;

        setError(null);
        setLoadingContent(true);
        setContent("");
        setHeatStats(null);
        if (editorRef.current && decorationsRef.current.length > 0) {
            editorRef.current.deltaDecorations(decorationsRef.current, []);
            decorationsRef.current = [];
        }

        getFileContent(repoUrl, activeFile)
            .then(text => {
                setContent(text || "");
                setLoadingContent(false);
            })
            .catch(err => {
                setError(`Failed to load file: ${err.message}`);
                setLoadingContent(false);
            });
    }, [activeFile, repoUrl]);

    useEffect(() => {
        if (!activeFile || !repoUrl || loadingContent || !content) return;

        setLoadingHeat(true);

        Promise.all([
            getLineHeatmap(repoUrl, activeFile, timeWindow),
            getFileMetrics(repoUrl, activeFile, timeWindow).catch(() => null),
        ])
            .then(([heatmapData, metrics]) => {
                setLoadingHeat(false);
                if (!editorRef.current || !monacoRef.current) return;

                const heatmap = heatmapData?.heatmap || [];
                const decos = buildDecorations(heatmap, metrics, heatmapMode, isSmoothed);

                const newDecoIds = editorRef.current.deltaDecorations(
                    decorationsRef.current,
                    decos.map(d => ({
                        range: new monacoRef.current.Range(
                            d.range.startLineNumber, 1,
                            d.range.endLineNumber, 1
                        ),
                        options: d.options,
                    }))
                );
                decorationsRef.current = newDecoIds;

                const hotLines = heatmap.filter(l => l.modification_count > 0).length;
                const maxCount = Math.max(...heatmap.map(l => l.modification_count), 0);
                setHeatStats({ hotLines, maxCount, total: heatmap.length });
            })
            .catch(() => setLoadingHeat(false));
    }, [content, activeFile, repoUrl, loadingContent, timeWindow, heatmapMode, isSmoothed]);

    const handleEditorDidMount = useCallback((editor, monaco) => {
        editorRef.current = editor;
        monacoRef.current = monaco;
    }, []);

    const language = detectLanguage(activeFile);
    const fileName = activeFile ? activeFile.split("/").pop() : "";

    // ── Empty state ──────────────────────────────────────────────────────────
    if (!openFiles || openFiles.length === 0) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center bg-[#000000] text-center gap-4">
                <CodeIcon size={48} className="text-[#27272a]" />
                <p className="text-[#71717a] text-sm">Select a file from the explorer to begin.</p>
                <p className="text-[#3f3f46] text-xs font-mono">Lines will be heatmapped based on modification frequency.</p>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col bg-[#000000] min-w-0 relative">
            {/* VS Code Style Tab Bar */}
            <div className="flex w-full overflow-x-auto bg-[#000000] border-b border-[#27272a] scrollbar-none flex-shrink-0">
                {openFiles.map(file => {
                    const isActive = file === activeFile;
                    const name = file.split('/').pop();
                    return (
                        <div
                            key={file}
                            onClick={() => onFileSelect(file)}
                            className={`flex items-center gap-2 px-3 py-2 border-r border-[#27272a] cursor-pointer min-w-[120px] max-w-[200px] border-t-2 ${isActive ? 'bg-[#18181b] border-t-white text-white' : 'bg-[#000000] border-t-transparent text-[#a1a1aa] hover:bg-[#18181b]'} transition-colors group select-none`}
                        >
                            <FileIcon size={12} className={isActive ? "text-[#a1a1aa]" : "text-[#71717a]"} />
                            <span className="truncate flex-1 text-xs font-mono">{name}</span>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onFileClose(file);
                                }}
                                className={`p-0.5 rounded text-[#71717a] hover:bg-[#27272a] hover:text-[#e5e5e5] ${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
                            >
                                <XIcon size={12} />
                            </button>
                        </div>
                    );
                })}
            </div>

            {/* File path breadcrumb & Active Stats */}
            <div className="px-4 py-1.5 text-[10px] font-mono text-[#52525b] border-b border-[#27272a] bg-[#000000] flex items-center justify-between flex-shrink-0">
                <div className="flex items-center truncate">
                    {activeFile.split('/').map((segment, i, arr) => (
                        <div key={i} className="flex items-center">
                            <span className={i === arr.length - 1 ? "text-[#e5e5e5]" : "text-[#71717a] cursor-pointer hover:text-[#a1a1aa]"}>
                                {segment}
                            </span>
                            {i < arr.length - 1 && <ChevronRightIcon size={12} className="mx-1 text-[#3f3f46]" />}
                        </div>
                    ))}
                </div>
                <div className="flex items-center gap-4 text-[10px] font-mono text-[#52525b] uppercase tracking-wider ml-4 shrink-0">
                    <select
                        value={heatmapMode}
                        onChange={e => setHeatmapMode(e.target.value)}
                        className="bg-[#18181b] border border-[#27272a] text-[#a1a1aa] px-2 py-0.5 rounded outline-none hover:text-white cursor-pointer"
                    >
                        <option value="intensity">Intensity Mode</option>
                        <option value="volatility">Volatility Mode</option>
                        <option value="recency">Recency Mode</option>
                    </select>

                    <label className="flex items-center gap-1 cursor-pointer text-[#a1a1aa] hover:text-white border-r border-[#27272a] pr-4">
                        <input
                            type="checkbox"
                            checked={isSmoothed}
                            onChange={e => setIsSmoothed(e.target.checked)}
                            className="accent-white cursor-pointer m-0 p-0"
                            style={{ width: '10px', height: '10px' }}
                        />
                        Smooth
                    </label>

                    {heatStats && (
                        <div className="flex items-center gap-2 border-r border-[#27272a] pr-4">
                            <span className="text-red-400 font-medium">{heatStats.hotLines} edited lines</span>
                            <span>max {heatStats.maxCount}×</span>
                        </div>
                    )}
                    <span>{language}</span>
                    {loadingHeat && (
                        <span className="flex items-center gap-2 text-white bg-[#27272a] px-2 py-0.5 rounded">
                            <LoaderIcon size={10} />
                            heatmapping
                        </span>
                    )}
                </div>
            </div>

            {/* Editor area */}
            <div className="flex-1 relative overflow-hidden bg-[#000000]">
                {loadingContent && <LoadingOverlay message="Loading file content" />}
                {error && (
                    <div className="absolute inset-0 flex items-center justify-center z-10 bg-[#000000]/80">
                        <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-4 text-[#e5e5e5] text-sm font-mono max-w-lg text-center shadow-2xl">
                            {error}
                        </div>
                    </div>
                )}

                {heatStats && heatStats.hotLines === 0 && !loadingHeat && (
                    <div className="absolute inset-x-0 top-0 h-48 bg-gradient-to-b from-[#0a0a0a] to-transparent z-10 p-6 pointer-events-none flex flex-col justify-start items-center">
                        <div className="bg-[#18181b]/90 backdrop-blur-sm border border-[#27272a] rounded-full px-4 py-2 flex items-center gap-3 shadow-lg pointer-events-auto">
                            <CheckCircleIcon size={16} className="text-emerald-500" />
                            <span className="text-xs text-[#a1a1aa]">No instability detected in selected time window. This file is historically stable.</span>
                        </div>
                    </div>
                )}

                <Editor
                    value={content}
                    language={language}
                    theme="vs-dark"
                    options={EDITOR_OPTIONS}
                    onMount={handleEditorDidMount}
                    loading={
                        <div className="flex items-center justify-center h-full text-[#52525b] text-xs font-mono uppercase tracking-widest">
                            Loading Editor Segment
                        </div>
                    }
                />
            </div>
        </div>
    );
}
