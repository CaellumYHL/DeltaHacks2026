import React, { useState } from "react";
import {
  Telescope,
  TrendingUp,
  Map as MapIcon,
  Star,
  Activity
} from "lucide-react";

/* ---------------- UI HELPERS ---------------- */

const GlassPanel = ({ children, className = "" }) => (
  <div
    className={`backdrop-blur-xl bg-white/[0.03] border border-white/10 rounded-2xl shadow-2xl ${className}`}
  >
    {children}
  </div>
);

const ViewHeader = ({ title, subtitle, icon: Icon }) => (
  <div className="flex items-center gap-4 mb-6">
    <div className="p-3 bg-white/5 rounded-xl border border-white/10">
      <Icon className="w-6 h-6 text-white" />
    </div>
    <div>
      <h1 className="text-2xl font-bold text-white">{title}</h1>
      <p className="text-xs uppercase tracking-widest text-gray-400">
        {subtitle}
      </p>
    </div>
  </div>
);

/* ---------------- MAIN APP ---------------- */

export default function App() {
  const [activeView, setActiveView] = useState("map");
  const [galaxyUrl, setGalaxyUrl] = useState(null);
  const [loadingGalaxy, setLoadingGalaxy] = useState(false);

  const [query, setQuery] = useState("");
  const [aiResponse, setAiResponse] = useState("");

  /* -------- API CALLS -------- */

  const launchGalaxy = async () => {
    setLoadingGalaxy(true);

    const res = await fetch("http://localhost:5000/api/galaxy/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: "Artificial Intelligence",
        threshold: 0.4,
        color_mode: "Cluster",
        use_mock: true
      })
    });

    const data = await res.json();
    setGalaxyUrl("http://localhost:5000" + data.html);
    setLoadingGalaxy(false);
  };

  const analyze = async () => {
    if (!query.trim()) return;

    const res = await fetch("http://localhost:5000/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });

    const data = await res.json();
    setAiResponse(data.response);
  };

  /* ---------------- RENDER ---------------- */

  return (
    <div className="min-h-screen bg-[#020408] text-slate-200 flex">
      {/* SIDEBAR */}
      <aside className="w-64 border-r border-white/10 bg-black/40 p-6">
        <div className="flex items-center gap-3 mb-10">
          <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center">
            <Star className="text-black" />
          </div>
          <div>
            <h2 className="font-bold text-white">N.C. SUITE</h2>
            <p className="text-xs text-gray-400">News Constellation</p>
          </div>
        </div>

        <nav className="space-y-2">
          <button
            onClick={() => setActiveView("map")}
            className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-white/5"
          >
            <MapIcon className="w-4 h-4" /> Constellation Map
          </button>
          <button
            onClick={() => setActiveView("ai")}
            className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-white/5"
          >
            <TrendingUp className="w-4 h-4" /> AI Analyst
          </button>
          <button
            onClick={() => setActiveView("galaxy")}
            className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-white/5"
          >
            <Telescope className="w-4 h-4" /> Galaxy Graph
          </button>
        </nav>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 p-10 overflow-hidden">
        {/* ---------------- GALAXY ---------------- */}
        {activeView === "galaxy" && (
          <>
            <ViewHeader
              title="Galaxy Graph"
              subtitle="Semantic article topology"
              icon={Telescope}
            />

            <GlassPanel className="h-[75vh] flex items-center justify-center">
              {!galaxyUrl ? (
                <button
                  onClick={launchGalaxy}
                  disabled={loadingGalaxy}
                  className="px-6 py-3 bg-white text-black rounded-lg font-bold"
                >
                  {loadingGalaxy ? "Scanning Cosmos…" : "🚀 Launch Galaxy"}
                </button>
              ) : (
                <iframe
                  src={galaxyUrl}
                  title="Galaxy Graph"
                  className="w-full h-full rounded-xl border-none"
                />
              )}
            </GlassPanel>
          </>
        )}

        {/* ---------------- AI ANALYST ---------------- */}
        {activeView === "ai" && (
          <>
            <ViewHeader
              title="AI Analyst"
              subtitle="Cross-article reasoning engine"
              icon={Activity}
            />

            <GlassPanel className="p-6 max-w-3xl">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask the galaxy a question…"
                className="w-full p-3 rounded-lg bg-black/60 border border-white/10 text-white"
              />

              <button
                onClick={analyze}
                className="mt-4 px-5 py-2 bg-white text-black rounded-lg font-semibold"
              >
                Analyze
              </button>

              {aiResponse && (
                <p className="mt-6 text-gray-200 whitespace-pre-line">
                  {aiResponse}
                </p>
              )}
            </GlassPanel>
          </>
        )}

        {/* ---------------- MAP PLACEHOLDER ---------------- */}
        {activeView === "map" && (
          <>
            <ViewHeader
              title="Constellation Map"
              subtitle="Global article distribution"
              icon={MapIcon}
            />
            <GlassPanel className="p-10 opacity-60">
              🌍 Map view ready — connect deck.gl here if needed.
            </GlassPanel>
          </>
        )}
      </main>
    </div>
  );
}
