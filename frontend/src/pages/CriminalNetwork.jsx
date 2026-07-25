import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { Network } from "vis-network";
import { DataSet } from "vis-data";
import {
  Users, Share2, GitBranch, Repeat, Search, Zap, ChevronRight,
  X, UserX, AlertTriangle, MapPin,
  Eye, EyeOff, Layers, Info,
} from "lucide-react";
import PageShell from "../components/PageShell";
import { getNetwork } from "../services/networkService";
import { T } from "../styles/theme";

// ─── Node Type Configuration ──────────────────────────────────
const NODE_TYPES = {
  accused: {
    label: "Accused", color: "#EF4444", bg: "rgba(239,68,68,0.15)",
    border: "#EF4444", shape: "diamond", icon: "🔴",
  },
  victim: {
    label: "Victim", color: "#22C55E", bg: "rgba(34,197,94,0.15)",
    border: "#22C55E", shape: "dot", icon: "🟢",
  },
  fir: {
    label: "FIR", color: "#4F8CFF", bg: "rgba(79,140,255,0.15)",
    border: "#4F8CFF", shape: "box", icon: "🔵",
  },
  evidence: {
    label: "Evidence", color: "#F59E0B", bg: "rgba(245,158,11,0.15)",
    border: "#F59E0B", shape: "hexagon", icon: "🟡",
  },
  financial_transaction: {
    label: "Financial", color: "#06B6D4", bg: "rgba(6,182,212,0.15)",
    border: "#06B6D4", shape: "diamond", icon: "🔷",
  },
  location: {
    label: "Location", color: "#8B5CF6", bg: "rgba(139,92,246,0.15)",
    border: "#8B5CF6", shape: "triangle", icon: "🟣",
  },
  crime_type: {
    label: "Crime Type", color: "#EC4899", bg: "rgba(236,72,153,0.15)",
    border: "#EC4899", shape: "star", icon: "🩷",
  },
  phone: {
    label: "Phone", color: "#94A3B8", bg: "rgba(148,163,184,0.15)",
    border: "#94A3B8", shape: "dot", icon: "⚪",
  },
  vehicle: {
    label: "Vehicle", color: "#F97316", bg: "rgba(249,115,22,0.15)",
    border: "#F97316", shape: "square", icon: "🟠",
  },
  bank_account: {
    label: "Bank Account", color: "#14B8A6", bg: "rgba(20,184,166,0.15)",
    border: "#14B8A6", shape: "diamond", icon: "🟩",
  },
};

const DEFAULT_NODE = {
  label: "Unknown", color: "#94A3B8", bg: "rgba(148,163,184,0.15)",
  border: "#94A3B8", shape: "dot", icon: "⚪",
};

// ─── Relationship Descriptions ────────────────────────────────
const EDGE_LABELS = {
  has_victim: "Victim of", has_accused: "Accused in", co_accused: "Co-accused",
  occurred_at: "Occurred at", involves_crime: "Crime type", has_phone: "Phone",
  has_evidence: "Has evidence", has_vehicle: "Vehicle in evidence",
  has_financial: "Financial transaction", financial_link: "Financial link",
  uses_account: "Uses account", has_transaction: "Transaction",
  owns_account: "Account owner", linked_fir: "Linked FIR",

};

function getRiskColor(score) {
  if (!score || score === 0) return null;
  if (score >= 8) return { bg: "rgba(220,38,38,0.25)", border: "#DC2626", glow: "rgba(220,38,38,0.5)" };
  if (score >= 5) return { bg: "rgba(234,88,12,0.20)", border: "#EA580C", glow: "rgba(234,88,12,0.4)" };
  if (score >= 3) return { bg: "rgba(234,179,8,0.18)", border: "#EAB308", glow: "rgba(234,179,8,0.3)" };
  return { bg: "rgba(34,197,94,0.15)", border: "#22C55E", glow: "rgba(34,197,94,0.2)" };
}

// ─── Sub-components ───────────────────────────────────────────

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div style={{
      background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 20,
      transition: "all 0.2s",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
        <div style={{
          width: 40, height: 40, borderRadius: 12,
          background: `${color}15`, display: "flex",
          alignItems: "center", justifyContent: "center",
        }}>
          <Icon size={20} color={color} />
        </div>
        <span style={{ color: T.textMuted, fontSize: 13 }}>{label}</span>
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: T.textPrimary }}>{value}</div>
    </div>
  );
}

function SkeletonBlock({ height = 400, width = "100%" }) {
  return (
    <div style={{
      height, width, background: T.card, border: `1px solid ${T.cardBorder}`,
      borderRadius: 16, animation: "pulse 2s infinite",
    }} />
  );
}

function NetworkLegend({ nodeCounts }) {
  const visibleTypes = Object.entries(NODE_TYPES).filter(
    ([key]) => nodeCounts[key] > 0 || key === "accused" || key === "fir"
  );

  return (
    <div style={{
      background: T.card, border: `1px solid ${T.cardBorder}`,
      borderRadius: 12, padding: 14,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
        <Layers size={14} color={T.accent} />
        <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>
          Network Legend
        </span>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {visibleTypes.map(([key, cfg]) => (
          <div key={key} style={{
            display: "flex", alignItems: "center", gap: 5,
            padding: "4px 8px", borderRadius: 6,
            background: cfg.bg, border: `1px solid ${cfg.color}33`,
          }}>
            <span style={{
              width: 8, height: 8, borderRadius: cfg.shape === "box" ? 2 : "50%",
              background: cfg.color, flexShrink: 0,
            }} />
            <span style={{ color: cfg.color, fontSize: 10, fontWeight: 600 }}>
              {cfg.label}
            </span>
            {nodeCounts[key] > 0 && (
              <span style={{ color: T.textMuted, fontSize: 9 }}>
                {nodeCounts[key]}
              </span>
            )}
          </div>
        ))}
      </div>
      {/* Relationship types */}
      <div style={{ marginTop: 8 }}>
        <div style={{ color: T.textMuted, fontSize: 9, fontWeight: 600, marginBottom: 4 }}>
          Relationships
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {["Accused ↔ FIR", "Victim ↔ FIR", "Evidence ↔ FIR", "Accused ↔ Financial"].map((rel) => (
            <span key={rel} style={{
              fontSize: 9, color: T.textMuted, padding: "2px 6px",
              background: T.inputBg, borderRadius: 4,
            }}>
              {rel}
            </span>
          ))}
        </div>
      </div>
      {/* Risk indicator */}
      <div style={{ marginTop: 8 }}>
        <div style={{ color: T.textMuted, fontSize: 9, fontWeight: 600, marginBottom: 4 }}>
          Risk Score
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {[
            { label: "Low", color: "#22C55E" },
            { label: "Med", color: "#EAB308" },
            { label: "High", color: "#EA580C" },
            { label: "Crit", color: "#DC2626" },
          ].map((r) => (
            <div key={r.label} style={{
              display: "flex", alignItems: "center", gap: 3,
            }}>
              <span style={{
                width: 6, height: 6, borderRadius: "50%",
                background: r.color,
              }} />
              <span style={{ color: T.textMuted, fontSize: 9 }}>{r.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────

export default function CriminalNetwork({ user }) {
  const containerRef = useRef(null);
  const networkInstance = useRef(null);

  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [firFilter, setFirFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selectedNode, setSelectedNode] = useState(null);
  const [insights, setInsights] = useState([]);
  const [showLegend, setShowLegend] = useState(true);
  const searchTimer = useRef(null);

  // ── Compute node counts for legend ─────────────────────────
  const nodeCounts = useMemo(() => {
    if (!graphData?.nodes) return {};
    const counts = {};
    graphData.nodes.forEach((n) => {
      counts[n.type] = (counts[n.type] || 0) + 1;
    });
    return counts;
  }, [graphData]);

  // ── Fetch network data ─────────────────────────────────────
  const fetchNetwork = useCallback(async () => {
    setLoading(true);
    setError("");
    setSelectedNode(null);
    setSearch("");
    try {
      const data = await getNetwork(firFilter || null);
      setGraphData(data);
      generateInsights(data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to load criminal network");
      setGraphData(null);
    } finally {
      setLoading(false);
    }
  }, [firFilter]);

  useEffect(() => { fetchNetwork(); }, [fetchNetwork]);

  // ── Generate insights ──────────────────────────────────────
  const generateInsights = (data) => {
    if (!data?.statistics) { setInsights([]); return; }
    const s = data.statistics;
    const ins = [];
    if (s.total_criminals > 0) {
      ins.push({
        icon: Users, text: `${s.total_criminals} known criminals identified in the network.`,
        impact: "info", color: "#4F8CFF",
      });
    }
    if (s.repeat_offenders > 0) {
      ins.push({
        icon: Repeat, text: `${s.repeat_offenders} repeat offenders linked to multiple FIRs.`,
        impact: "danger", color: "#EF4444",
      });
    }
    if (s.top_association) {
      ins.push({
        icon: Share2, text: `Most common relationship: "${s.top_association}" (${s.total_connections} total connections).`,
        impact: "warning", color: "#F59E0B",
      });
    }
    if (s.largest_network > 10) {
      ins.push({
        icon: GitBranch, text: `Largest criminal network contains ${s.largest_network} entities — requires focused investigation.`,
        impact: "danger", color: "#EF4444",
      });
    }
    if (s.active_networks > 1) {
      ins.push({
        icon: GitBranch, text: `${s.active_networks} distinct network clusters detected across the dataset.`,
        impact: "info", color: "#4F8CFF",
      });
    }
    setInsights(ins);
  };

  // ── Render vis-network ─────────────────────────────────────
  useEffect(() => {
    if (!graphData || !containerRef.current || !graphData.nodes?.length) return;

    const nodes = new DataSet(graphData.nodes.map((n) => {
      const nt = NODE_TYPES[n.type] || DEFAULT_NODE;
      let nodeColor = nt.color;
      let nodeBg = nt.bg;
      let nodeBorder = nt.border;
      let borderWidth = 2;

      // Risk-based coloring for accused nodes
      if (n.type === "accused" && n.metadata?.risk_score) {
        const riskScore = parseFloat(n.metadata.risk_score);
        const risk = getRiskColor(riskScore);
        if (risk) {
          nodeBg = risk.bg;
          nodeBorder = risk.border;
          borderWidth = riskScore >= 8 ? 3 : 2;
        }
      }

      return {
        id: n.id,
        label: n.label,
        title: `<div style="padding:6px 0;font-family:Inter,sans-serif;">
          <b style="font-size:13px;">${n.label}</b><br/>
          <span style="color:#94A3B8;font-size:11px;">Type: ${nt.label}</span>
          ${n.metadata?.risk_score ? `<br/><span style="color:${nodeBorder};font-size:11px;">Risk: ${n.metadata.risk_score}/10</span>` : ""}
        </div>`,
        color: {
          background: nodeBg,
          border: nodeBorder,
          highlight: { background: nodeBorder + "44", border: nodeBorder },
          hover: { background: nodeBorder + "33", border: nodeBorder },
        },
        borderWidth,
        borderWidthSelected: 3,
        font: {
          color: T.textPrimary, size: 11, face: "Inter, sans-serif",
          strokeWidth: 1, strokeColor: "#0D1320",
        },
        size: n.type === "accused" ? 28 : n.type === "fir" ? 22 : n.type === "evidence" ? 18 : 15,
        shape: nt.shape,
        ...(n.metadata?.risk_score && {
          shadow: {
            enabled: true,
            color: nodeBorder + "66",
            size: Math.min(parseFloat(n.metadata.risk_score) * 2, 20),
            x: 0, y: 0,
          },
        }),
      };
    }));

    const edges = new DataSet(graphData.edges.map((e) => ({
      id: e.id,
      from: e.source,
      to: e.target,
      label: EDGE_LABELS[e.label] || e.label,
      width: Math.max(1, (e.weight || 1) * 1.5),
      color: {
        color: "rgba(148,163,184,0.35)",
        highlight: T.accent,
        hover: T.accent,
        inherit: false,
        opacity: 0.8,
      },
      font: {
        color: T.textMuted, size: 8, strokeWidth: 2,
        strokeColor: "#0D1320", align: "middle",
      },
      smooth: {
        type: "continuous",
        roundness: 0.3,
      },
      // Animated edges via physics
      physics: true,
      hoverWidth: 2,
      selectionWidth: 2,
      arrows: {
        to: { enabled: true, scaleFactor: 0.6, type: "arrow" },
      },
    })));

    const options = {
      nodes: {
        scaling: { min: 12, max: 45 },
        margin: { top: 6, bottom: 6, left: 8, right: 8 },
      },
      edges: {
        scaling: { min: 1, max: 8 },
        smooth: { type: "continuous", roundness: 0.3 },
      },
      physics: {
        solver: "forceAtlas2Based",
        forceAtlas2Based: {
          gravitationalConstant: -35,
          centralGravity: 0.004,
          springLength: 150,
          springConstant: 0.018,
          damping: 0.5,
        },
        stabilization: {
          iterations: 150,
          updateInterval: 25,
        },
        adaptiveTimestep: true,
      },
      interaction: {
        hover: true,
        tooltipDelay: 150,
        navigationButtons: true,
        keyboard: {
          enabled: true,
          bindToWindow: false,
        },
        selectConnectedEdges: true,
        hoverConnectedEdges: true,
        zoomView: true,
        dragView: true,
      },
      layout: {
        improvedLayout: true,
        randomSeed: 42,
      },
      groups: {
        person: { color: { background: "#EF444422", border: "#EF4444" } },
        case: { shape: "box", color: { background: "#4F8CFF22", border: "#4F8CFF" } },
        document: { shape: "hexagon", color: { background: "#F59E0B22", border: "#F59E0B" } },
        financial: { shape: "diamond", color: { background: "#06B6D422", border: "#06B6D4" } },
        place: { shape: "triangle", color: { background: "#8B5CF622", border: "#8B5CF6" } },
        category: { shape: "star", color: { background: "#EC489922", border: "#EC4899" } },
        contact: { shape: "dot", color: { background: "#94A3B822", border: "#94A3B8" } },
        asset: { shape: "square", color: { background: "#F9731622", border: "#F97316" } },
      },
      height: "100%",
      width: "100%",
    };

    networkInstance.current = new Network(containerRef.current, { nodes, edges }, options);

    // ── Event handlers ───────────────────────────────────────
    networkInstance.current.on("click", (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = graphData.nodes.find((n) => n.id === nodeId);
        if (node) {
          const neighbors = graphData.edges
            .filter((e) => e.source === nodeId || e.target === nodeId)
            .map((e) => ({
              edge: e,
              neighbor: e.source === nodeId ? e.target : e.source,
            }));
          const neighborNodes = neighbors
            .map((nn) => graphData.nodes.find((n) => n.id === nn.neighbor))
            .filter(Boolean);
          setSelectedNode({ node, neighbors, neighborNodes });
        }
      } else {
        setSelectedNode(null);
      }
    });

    networkInstance.current.on("doubleClick", () => {
      if (networkInstance.current) {
        networkInstance.current.fit({ animation: true });
      }
    });

    // Fit to screen after stabilization
    const fitTimer = setTimeout(() => {
      if (networkInstance.current) {
        networkInstance.current.fit({ animation: true, duration: 300 });
      }
    }, 2000);

    // ── Cleanup ──────────────────────────────────────────────
    return () => {
      clearTimeout(fitTimer);
      if (networkInstance.current) {
        networkInstance.current.destroy();
        networkInstance.current = null;
      }
    };
  }, [graphData, T]);

  // ── Search (debounced) ─────────────────────────────────────
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      if (!networkInstance.current || !graphData?.nodes) return;
      const net = networkInstance.current;
      if (!search.trim()) {
        net.setSelection([]);
        return;
      }
      const q = search.toLowerCase();
      const matchingIds = graphData.nodes
        .filter(
          (n) =>
            n.label.toLowerCase().includes(q) ||
            (n.type || "").toLowerCase().includes(q) ||
            (NODE_TYPES[n.type]?.label || "").toLowerCase().includes(q)
        )
        .map((n) => n.id);
      if (matchingIds.length > 0) {
        try {
          net.selectNodes(matchingIds, false);
          net.focus(matchingIds[0], { scale: 1.3, animation: true });
        } catch (e) {
          // Ignore vis focus errors
        }
      }
    }, 200);
    return () => clearTimeout(searchTimer.current);
  }, [search, graphData]);

  const stats = graphData?.statistics;
  const showGraph = graphData && graphData.nodes?.length > 0;

  return (
    <PageShell title="Criminal Network Analysis" user={user}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        @keyframes slideUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
        @keyframes fadeIn { from{opacity:0} to{opacity:1} }
        .vis-network { background: transparent !important; }
        .vis-tooltip {
          background: ${T.card} !important;
          border: 1px solid ${T.cardBorder} !important;
          border-radius: 10px !important;
          padding: 8px 12px !important;
          font-family: inherit !important;
          box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
        }
        .vis-button {
          background: ${T.card} !important;
          border: 1px solid ${T.cardBorder} !important;
          border-radius: 8px !important;
          color: ${T.textSecondary} !important;
          font-size: 11px !important;
          padding: 4px 8px !important;
          box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
        }
        .vis-button:hover {
          background: ${T.accentGlow} !important;
          border-color: ${T.accent}44 !important;
        }
      `}</style>

      {/* ── Header ──────────────────────────────────────────── */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 20, flexWrap: "wrap", gap: 12,
      }}>
        <div>
          <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: 0 }}>
            Criminal Network Analysis
          </h1>
          <p style={{ color: T.textMuted, fontSize: 13, marginTop: 4 }}>
            Interactive relationship graph of accused, victims, FIRs, evidence, and financial transactions
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <div style={{ position: "relative" }}>
            <input
              type="text"
              placeholder="Search nodes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                padding: "8px 12px 8px 32px", borderRadius: 10,
                border: `1px solid ${T.cardBorder}`,
                background: T.inputBg, color: T.textPrimary,
                fontSize: 13, width: 200, outline: "none",
              }}
            />
            <Search size={14} color={T.textMuted} style={{
              position: "absolute", left: 10, top: "50%",
              transform: "translateY(-50%)",
            }} />
          </div>
          <button
            onClick={() => setShowLegend(!showLegend)}
            title="Toggle legend"
            style={{
              padding: "8px 10px", borderRadius: 10,
              border: `1px solid ${T.cardBorder}`,
              background: showLegend ? T.accentGlow : T.inputBg,
              color: showLegend ? T.accent : T.textSecondary,
              cursor: "pointer", fontSize: 14, lineHeight: 1,
              transition: "all 0.15s",
            }}
          >
            {showLegend ? <Eye size={16} /> : <EyeOff size={16} />}
          </button>
        </div>
      </div>

      {/* ── KPI Cards ────────────────────────────────────────── */}
      {!loading && stats && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 16, marginBottom: 20,
        }}>
          <StatCard icon={Users} label="Known Criminals" value={stats.total_criminals} color="#EF4444" />
          <StatCard icon={Share2} label="Total Connections" value={stats.total_connections} color="#4F8CFF" />
          <StatCard icon={GitBranch} label="Largest Network" value={stats.largest_network} color="#8B5CF6" />
          <StatCard icon={Repeat} label="Repeat Offenders" value={stats.repeat_offenders} color="#F59E0B" />
        </div>
      )}

      {loading && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 16, marginBottom: 20,
        }}>
          {[1, 2, 3, 4].map((i) => <SkeletonBlock key={i} height={100} />)}
        </div>
      )}

      {/* ── Filters Bar ──────────────────────────────────────── */}
      <div style={{
        display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap",
        padding: 14, background: T.card, borderRadius: 12,
        border: `1px solid ${T.cardBorder}`, alignItems: "center",
      }}>
        <MapPin size={16} color={T.textMuted} />
        <span style={{ color: T.textMuted, fontSize: 13, fontWeight: 600 }}>
          Filter by FIR:
        </span>
        <input
          type="text"
          placeholder="FIR ID or number..."
          value={firFilter}
          onChange={(e) => setFirFilter(e.target.value)}
          style={{
            padding: "6px 12px", borderRadius: 8,
            border: `1px solid ${T.cardBorder}`,
            background: T.inputBg, color: T.textPrimary,
            fontSize: 13, width: 180, outline: "none",
          }}
        />
        <button
          onClick={fetchNetwork}
          style={{
            padding: "6px 16px", borderRadius: 8, border: "none",
            background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`,
            color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600,
            display: "flex", alignItems: "center", gap: 6,
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-1px)";
            e.currentTarget.style.boxShadow = `0 4px 12px ${T.accent}44`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "none";
            e.currentTarget.style.boxShadow = "none";
          }}
        >
          <Zap size={14} /> Load Network
        </button>

        {/* Node type badges */}
        {showGraph && (
          <div style={{ display: "flex", gap: 4, marginLeft: "auto", flexWrap: "wrap" }}>
            {["accused", "victim", "fir", "evidence", "financial_transaction"].map((type) => {
              const cfg = NODE_TYPES[type];
              if (!nodeCounts[type]) return null;
              return (
                <span key={type} style={{
                  padding: "2px 8px", borderRadius: 12, fontSize: 10, fontWeight: 600,
                  background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}44`,
                }}>
                  {cfg.icon} {cfg.label} {nodeCounts[type]}
                </span>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Error State ──────────────────────────────────────── */}
      {error && !loading && (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", minHeight: 300, textAlign: "center",
          background: T.card, border: `1px solid ${T.cardBorder}`,
          borderRadius: 16, padding: 40,
        }}>
          <UserX size={48} color={T.danger} strokeWidth={1.5} />
          <p style={{ color: T.danger, fontSize: 15, margin: "16px 0 8px" }}>{error}</p>
          <p style={{ color: T.textMuted, fontSize: 13, marginBottom: 20 }}>
            Unable to build the criminal network graph.
          </p>
          <button
            onClick={fetchNetwork}
            style={{
              padding: "10px 24px", borderRadius: 10, border: "none",
              background: T.accent, color: "#fff", cursor: "pointer",
              fontSize: 14, fontWeight: 600,
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* ── Empty State ──────────────────────────────────────── */}
      {!loading && !error && graphData && !showGraph && (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", minHeight: 400, textAlign: "center",
          background: T.card, border: `1px solid ${T.cardBorder}`,
          borderRadius: 16, padding: 40,
        }}>
          <div style={{ fontSize: 64, marginBottom: 16 }}>🕸</div>
          <h3 style={{ color: T.textPrimary, fontSize: 18, margin: "0 0 8px" }}>
            No Criminal Network Data Found
          </h3>
          <p style={{ color: T.textMuted, fontSize: 14, maxWidth: 450, lineHeight: 1.6 }}>
            Create FIR records with linked accused persons, victims, and evidence to generate
            relationship graphs. The network is built dynamically from actual database relationships.
          </p>
          {graphData?.metadata?.message && (
            <p style={{ color: T.textMuted, fontSize: 12, marginTop: 8, fontStyle: "italic" }}>
              {graphData.metadata.message}
            </p>
          )}
          <button
            onClick={fetchNetwork}
            style={{
              marginTop: 20, padding: "10px 24px", borderRadius: 10,
              border: `1px solid ${T.accent}`, background: "transparent",
              color: T.accent, cursor: "pointer", fontSize: 14, fontWeight: 600,
              display: "flex", alignItems: "center", gap: 8,
            }}
          >
            <Zap size={16} /> Refresh Data
          </button>
        </div>
      )}

      {/* ── Main Content: Graph + Details ────────────────────── */}
      {!loading && !error && showGraph && (
        <div style={{
          display: "flex", gap: 20, marginBottom: 24,
          flexDirection: selectedNode ? "row" : "column",
        }}>
          {/* Left: Graph + Legend Column */}
          <div style={{
            flex: selectedNode ? 1.5 : 1,
            display: "flex", flexDirection: "column", gap: 16, minWidth: 0,
          }}>
            {/* Graph Container */}
            <div style={{
              background: T.card, border: `1px solid ${T.cardBorder}`,
              borderRadius: 16, overflow: "hidden", position: "relative",
            }}>
              <div style={{
                padding: "12px 16px", borderBottom: `1px solid ${T.cardBorder}`,
                display: "flex", justifyContent: "space-between", alignItems: "center",
              }}>
                <span style={{ color: T.textPrimary, fontSize: 14, fontWeight: 600 }}>
                  Interactive Network Graph
                </span>
                <span style={{ color: T.textMuted, fontSize: 11 }}>
                  Double-click to fit · Scroll to zoom · Click nodes for details
                </span>
              </div>
              <div
                ref={containerRef}
                style={{
                  height: "520px",
                  background: "radial-gradient(ellipse at center, #141B2D 0%, #0D1320 100%)",
                }}
              />
            </div>

            {/* Legend (collapsible) */}
            {showLegend && (
              <NetworkLegend nodeCounts={nodeCounts} />
            )}
          </div>

          {/* Right: Details Panel */}
          {selectedNode && (
            <div style={{
              flex: 1, minWidth: 300, maxWidth: 420,
              background: T.card, border: `1px solid ${T.cardBorder}`,
              borderRadius: 16, animation: "slideUp 0.3s ease",
              maxHeight: 600, overflowY: "auto",
              position: "sticky", top: 20, alignSelf: "flex-start",
            }}>
              <div style={{
                padding: "14px 16px", borderBottom: `1px solid ${T.cardBorder}`,
                display: "flex", justifyContent: "space-between",
                alignItems: "center", position: "sticky", top: 0,
                background: T.card, zIndex: 1,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
                  <div style={{
                    width: 10, height: 10, borderRadius: "50%",
                    background: (NODE_TYPES[selectedNode.node.type] || DEFAULT_NODE).color,
                    flexShrink: 0,
                  }} />
                  <h3 style={{
                    color: T.textPrimary, fontSize: 14, fontWeight: 600,
                    margin: 0, whiteSpace: "nowrap", overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}>
                    {selectedNode.node.label}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedNode(null)}
                  style={{
                    padding: 4, borderRadius: 6, border: "none",
                    background: "transparent", color: T.textMuted,
                    cursor: "pointer", flexShrink: 0,
                  }}
                >
                  <X size={15} />
                </button>
              </div>

              <div style={{ padding: 16 }}>
                {/* Type & Group badges */}
                <div style={{ display: "flex", gap: 6, marginBottom: 12, flexWrap: "wrap" }}>
                  <span style={{
                    padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600,
                    background: (NODE_TYPES[selectedNode.node.type] || DEFAULT_NODE).bg,
                    color: (NODE_TYPES[selectedNode.node.type] || DEFAULT_NODE).color,
                  }}>
                    {(NODE_TYPES[selectedNode.node.type] || DEFAULT_NODE).icon}{" "}
                    {(NODE_TYPES[selectedNode.node.type] || DEFAULT_NODE).label}
                  </span>
                  {selectedNode.node.group && selectedNode.node.group !== selectedNode.node.type && (
                    <span style={{
                      padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600,
                      background: "rgba(148,163,184,0.15)", color: "#94A3B8",
                    }}>
                      {selectedNode.node.group}
                    </span>
                  )}
                  {/* Risk badge for accused */}
                  {selectedNode.node.type === "accused" && selectedNode.node.metadata?.risk_score && (
                    <span style={{
                      padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600,
                      background: (() => {
                        const s = parseFloat(selectedNode.node.metadata.risk_score);
                        if (s >= 8) return "rgba(220,38,38,0.2)";
                        if (s >= 5) return "rgba(234,88,12,0.2)";
                        return "rgba(34,197,94,0.2)";
                      })(),
                      color: (() => {
                        const s = parseFloat(selectedNode.node.metadata.risk_score);
                        if (s >= 8) return "#DC2626";
                        if (s >= 5) return "#EA580C";
                        return "#22C55E";
                      })(),
                    }}>
                      Risk: {selectedNode.node.metadata.risk_score}/10
                    </span>
                  )}
                </div>

                {/* Metadata */}
                {selectedNode.node.metadata && Object.keys(selectedNode.node.metadata).length > 0 && (
                  <div style={{
                    display: "flex", flexDirection: "column", gap: 6,
                    marginBottom: 16,
                  }}>
                    {Object.entries(selectedNode.node.metadata).map(([key, val]) => {
                      if (!val || val === "null" || val === "None" || val === "") return null;
                      return (
                        <div key={key} style={{
                          display: "flex", justifyContent: "space-between",
                          padding: "4px 0", borderBottom: `1px solid ${T.cardBorder}`,
                        }}>
                          <span style={{
                            color: T.textMuted, fontSize: 11,
                            textTransform: "capitalize",
                          }}>
                            {key.replace(/_/g, " ")}
                          </span>
                          <span style={{
                            color: T.textPrimary, fontSize: 12, fontWeight: 500,
                            textAlign: "right", maxWidth: "60%",
                            wordBreak: "break-word",
                          }}>
                            {String(val)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Connections */}
                <h4 style={{
                  color: T.textMuted, fontSize: 11, fontWeight: 600,
                  margin: "0 0 8px", textTransform: "uppercase",
                  letterSpacing: 0.5, display: "flex",
                  alignItems: "center", gap: 6,
                }}>
                  <Share2 size={12} />
                  Connections ({selectedNode.neighbors?.length || 0})
                </h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {selectedNode.neighbors?.slice(0, 20).map((nn, i) => {
                    const nNode = selectedNode.neighborNodes[i];
                    if (!nNode) return null;
                    const nt = NODE_TYPES[nNode.type] || DEFAULT_NODE;
                    return (
                      <div key={i} style={{
                        display: "flex", alignItems: "center", gap: 8,
                        padding: "6px 8px", background: T.inputBg,
                        borderRadius: 8, transition: "all 0.15s",
                      }}>
                        <div style={{
                          width: 8, height: 8, borderRadius: nt.shape === "box" ? 2 : "50%",
                          background: nt.color, flexShrink: 0,
                        }} />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{
                            color: T.textPrimary, fontSize: 12, fontWeight: 500,
                            whiteSpace: "nowrap", overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}>
                            {nNode.label}
                          </div>
                          <div style={{ color: T.textMuted, fontSize: 10 }}>
                            {EDGE_LABELS[nn.edge.label] || nn.edge.label}
                            {nn.edge.weight ? ` · ${nn.edge.weight.toFixed(1)}` : ""}
                          </div>
                        </div>
                        <ChevronRight size={12} color={T.textMuted} />
                      </div>
                    );
                  })}
                  {(selectedNode.neighbors?.length || 0) > 20 && (
                    <div style={{
                      color: T.textMuted, fontSize: 11,
                      textAlign: "center", padding: 4,
                    }}>
                      +{selectedNode.neighbors.length - 20} more connections
                    </div>
                  )}
                </div>

                {/* AI Intelligence for node */}
                {selectedNode.node.type === "accused" && (
                  <div style={{
                    marginTop: 16, padding: 12, borderRadius: 10,
                    background: "rgba(239,68,68,0.08)",
                    border: "1px solid rgba(239,68,68,0.2)",
                  }}>
                    <div style={{
                      display: "flex", alignItems: "center", gap: 6,
                      marginBottom: 6,
                    }}>
                      <AlertTriangle size={14} color="#EF4444" />
                      <span style={{ color: "#EF4444", fontSize: 12, fontWeight: 600 }}>
                        AI Intelligence
                      </span>
                    </div>
                    <p style={{ color: T.textSecondary, fontSize: 12, lineHeight: 1.5, margin: 0 }}>
                      {selectedNode.node.metadata?.fir_count
                        ? `Linked to ${selectedNode.node.metadata.fir_count} FIR(s) with ${selectedNode.neighbors?.length || 0} connections.`
                        : "Connected to the criminal network through shared cases and associations."}
                      {selectedNode.node.metadata?.risk_score &&
                      parseFloat(selectedNode.node.metadata.risk_score) > 0
                        ? ` Risk score: ${selectedNode.node.metadata.risk_score}.`
                        : ""}
                      {selectedNode.node.metadata?.is_repeat_offender === "True"
                        ? " ⚠️ Repeat offender flagged."
                        : ""}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── AI Insights Panel ─────────────────────────────────── */}
      {!loading && insights.length > 0 && (
        <div style={{
          background: T.card, border: `1px solid ${T.cardBorder}`,
          borderRadius: 16, padding: 20, animation: "slideUp 0.4s ease",
        }}>
          <div style={{
            display: "flex", alignItems: "center", gap: 8, marginBottom: 16,
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: 10,
              background: "rgba(139,92,246,0.15)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Info size={16} color="#8B5CF6" />
            </div>
            <h3 style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600, margin: 0 }}>
              Network Intelligence
            </h3>
          </div>
          <div style={{
            display: "grid", gap: 10,
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
          }}>
            {insights.map((insight, i) => {
              const IconComponent = insight.icon;
              const isDanger = insight.impact === "danger";
              const isWarning = insight.impact === "warning";
              return (
                <div key={i} style={{
                  padding: 14, borderRadius: 12,
                  background: isDanger
                    ? "rgba(239,68,68,0.08)"
                    : isWarning
                      ? "rgba(245,158,11,0.08)"
                      : "rgba(79,140,255,0.08)",
                  border: `1px solid ${
                    isDanger
                      ? "rgba(239,68,68,0.2)"
                      : isWarning
                        ? "rgba(245,158,11,0.2)"
                        : "rgba(79,140,255,0.2)"
                  }`,
                  display: "flex", gap: 10, alignItems: "flex-start",
                }}>
                  <IconComponent size={18} color={insight.color} style={{ flexShrink: 0, marginTop: 1 }} />
                  <p style={{ color: T.textSecondary, fontSize: 12, lineHeight: 1.5, margin: 0 }}>
                    {insight.text}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </PageShell>
  );
}
