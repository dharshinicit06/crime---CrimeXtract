import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import { Search, X, MapPin, AlertTriangle } from "lucide-react";
import { getNetworkGraph } from "../../services/networkService";
import { T } from "../../styles/theme";

// ─── Node Type Styling ─────────────────────────────────────────
const NODE_STYLES = {
  FIR: {
    bg: "#4F8CFF22", border: "#4F8CFF", color: "#4F8CFF",
    shape: "rounded", icon: "🔵", size: { width: 160, height: 50 },
  },
  Accused: {
    bg: "#EF444422", border: "#EF4444", color: "#EF4444",
    shape: "diamond", icon: "🔴", size: { width: 140, height: 50 },
  },
  Victim: {
    bg: "#22C55E22", border: "#22C55E", color: "#22C55E",
    shape: "rounded", icon: "🟢", size: { width: 140, height: 50 },
  },
  Evidence: {
    bg: "#F59E0B22", border: "#F59E0B", color: "#F59E0B",
    shape: "hexagon", icon: "🟡", size: { width: 150, height: 50 },
  },
  Location: {
    bg: "#8B5CF622", border: "#8B5CF6", color: "#8B5CF6",
    shape: "rounded", icon: "🟣", size: { width: 150, height: 50 },
  },
  Transaction: {
    bg: "#06B6D422", border: "#06B6D4", color: "#06B6D4",
    shape: "diamond", icon: "🔷", size: { width: 150, height: 50 },
  },
};

const DEFAULT_STYLE = {
  bg: "#94A3B822", border: "#94A3B8", color: "#94A3B8",
  shape: "rounded", icon: "⚪", size: { width: 130, height: 45 },
};

// ─── Edge Styling ──────────────────────────────────────────────
const EDGE_STYLES = {
  INVOLVED_IN: { color: "#EF4444", label: "INVOLVED IN" },
  VICTIM_OF: { color: "#22C55E", label: "VICTIM OF" },
  EVIDENCE_FOR: { color: "#F59E0B", label: "EVIDENCE FOR" },
  OCCURRED_AT: { color: "#8B5CF6", label: "OCCURRED AT" },
  MONEY_TRANSFER: { color: "#06B6D4", label: "MONEY TRANSFER" },
};

// ─── Custom Node Component ─────────────────────────────────────
function NetworkNode({ data, selected }) {
  const style = NODE_STYLES[data.nodeType] || DEFAULT_STYLE;

  return (
    <div
      style={{
        padding: "8px 14px",
        borderRadius: style.shape === "diamond" ? 4 : 10,
        background: style.bg,
        border: `2px solid ${selected ? style.color : style.border}66`,
        boxShadow: selected
          ? `0 0 0 2px ${style.color}44, 0 4px 16px rgba(0,0,0,0.3)`
          : `0 2px 8px rgba(0,0,0,0.2)`,
        cursor: "pointer",
        transition: "all 0.2s",
        minWidth: 120,
        textAlign: "center",
        transform: style.shape === "diamond" ? "rotate(45deg)" : "none",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = style.color;
        e.currentTarget.style.boxShadow = `0 0 0 2px ${style.color}33, 0 6px 20px rgba(0,0,0,0.3)`;
      }}
      onMouseLeave={(e) => {
        if (!selected) {
          e.currentTarget.style.borderColor = style.border + "66";
          e.currentTarget.style.boxShadow = `0 2px 8px rgba(0,0,0,0.2)`;
        }
      }}
    >
      <div
        style={{
          transform: style.shape === "diamond" ? "rotate(-45deg)" : "none",
        }}
      >
        <div style={{ fontSize: 11, fontWeight: 700, color: style.color, marginBottom: 2 }}>
          {style.icon} {data.nodeType}
        </div>
        <div style={{ fontSize: 12, fontWeight: 600, color: "#E2E8F0", lineHeight: 1.3 }}>
          {data.label}
        </div>
        {data.riskScore > 0 && (
          <div style={{
            marginTop: 4, fontSize: 9, fontWeight: 600, color:
              data.riskScore >= 8 ? "#DC2626" : data.riskScore >= 5 ? "#EA580C" : data.riskScore >= 3 ? "#EAB308" : "#22C55E",
          }}>
            Risk: {data.riskScore}/10
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
    </div>
  );
}

const nodeTypes = { networkNode: NetworkNode };

// ─── Custom Edge Component ─────────────────────────────────────
const edgeOptions = {
  style: { strokeWidth: 2, opacity: 0.6 },
  markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
  animated: true,
};

// ─── Main Component ────────────────────────────────────────────
export default function CriminalNetwork({ firNumber: initialFir, onClose }) {
  const [firInput, setFirInput] = useState(initialFir || "");
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedNode, setSelectedNode] = useState(null);
  const [firNumber, setFirNumber] = useState(initialFir || "");
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);

  // ── Build graph from FIR number ─────────────────────────────
  const loadGraph = useCallback(async (fir) => {
    if (!fir?.trim()) return;
    setLoading(true);
    setError("");
    setSelectedNode(null);
    try {
      const data = await getNetworkGraph(fir.trim());
      if (data.error) {
        setError(data.error);
        setNodes([]);
        setEdges([]);
        return;
      }

      // Create React Flow nodes with positions
      const nodeTypesList = ["FIR", "Victim", "Evidence", "Location", "Transaction", "Accused"];
      const grouped = {};
      data.nodes.forEach((n) => {
        if (!grouped[n.type]) grouped[n.type] = [];
        grouped[n.type].push(n);
      });

      const rfNodes = [];
      const positions = {};
      const cols = 4;
      const hSpacing = 220;
      const vSpacing = 100;

      nodeTypesList.forEach((type) => {
        const items = grouped[type] || [];
        items.forEach((n, idx) => {
          const col = idx % cols;
          const row = Math.floor(idx / cols);
          const typeIndex = nodeTypesList.indexOf(n.type);
          const y = typeIndex * 180 + row * vSpacing;
          const x = col * hSpacing + 50;
          positions[n.id] = { x, y };
        });
      });

      data.nodes.forEach((n) => {
        const style = NODE_STYLES[n.type] || DEFAULT_STYLE;
        const pos = positions[n.id] || { x: Math.random() * 300, y: Math.random() * 300 };
        rfNodes.push({
          id: n.id,
          type: "networkNode",
          position: pos,
          data: {
            label: n.label,
            nodeType: n.type,
            metadata: n.metadata || {},
            riskScore: n.metadata?.risk_score || 0,
          },
        });
      });

      const rfEdges = data.edges.map((e, idx) => {
        const es = EDGE_STYLES[e.label] || { color: "#94A3B8", label: e.label };
        return {
          id: `e-${idx}`,
          source: e.source,
          target: e.target,
          label: es.label,
          type: "smoothstep",
          animated: true,
          style: { stroke: es.color, strokeWidth: 2, opacity: 0.7 },
          labelStyle: { fill: es.color, fontSize: 9, fontWeight: 600 },
          labelBgStyle: { fill: "#1E293B", fillOpacity: 0.8 },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: es.color,
            width: 16,
            height: 16,
          },
        };
      });

      setNodes(rfNodes);
      setEdges(rfEdges);
      setFirNumber(fir.trim());

      // Fit view after a short delay for layout
      setTimeout(() => {
        if (reactFlowInstance) {
          reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
        }
      }, 100);
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to load network graph");
      setNodes([]);
      setEdges([]);
    } finally {
      setLoading(false);
    }
  }, [reactFlowInstance, setNodes, setEdges]);

  useEffect(() => {
    if (initialFir) {
      loadGraph(initialFir);
    }
  }, [initialFir, loadGraph]);

  // ── Node click handler ──────────────────────────────────────
  const onNodeClick = useCallback((event, node) => {
    const graphNode = {
      id: node.id,
      label: node.data.label,
      type: node.data.nodeType,
      metadata: node.data.metadata,
    };

    // Find connected edges
    const connectedEdges = edges.filter(
      (e) => e.source === node.id || e.target === node.id
    );
    const neighborIds = new Set();
    connectedEdges.forEach((e) => {
      neighborIds.add(e.source === node.id ? e.target : e.source);
    });

    setSelectedNode({ node: graphNode, edges: connectedEdges, neighborIds });
  }, [edges]);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // ── Count by type for stats ─────────────────────────────────
  const stats = useMemo(() => {
    if (!nodes.length) return null;
    const counts = {};
    nodes.forEach((n) => {
      counts[n.data.nodeType] = (counts[n.data.nodeType] || 0) + 1;
    });
    return {
      totalNodes: nodes.length,
      totalEdges: edges.length,
      counts,
    };
  }, [nodes, edges]);

  const hasGraph = nodes.length > 0;

  return (
    <div style={{
      display: "flex", flexDirection: "column", gap: 16,
      height: "100%", minHeight: 500,
    }}>
      {/* ── FIR Input Bar ───────────────────────────────────── */}
      <div style={{
        display: "flex", gap: 10, alignItems: "center",
        padding: "12px 16px", background: T.card,
        border: `1px solid ${T.cardBorder}`, borderRadius: 12,
      }}>
        <MapPin size={16} color={T.textMuted} />
        <span style={{ color: T.textMuted, fontSize: 13, fontWeight: 600, whiteSpace: "nowrap" }}>
          FIR Number:
        </span>
        <input
          type="text"
          placeholder="e.g. FIR-2026-00001"
          value={firInput}
          onChange={(e) => setFirInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") loadGraph(firInput); }}
          style={{
            flex: 1, padding: "8px 12px", borderRadius: 8,
            border: `1px solid ${T.cardBorder}`, background: T.inputBg,
            color: T.textPrimary, fontSize: 13, outline: "none",
            maxWidth: 280,
          }}
        />
        <button
          onClick={() => loadGraph(firInput)}
          disabled={loading || !firInput.trim()}
          style={{
            padding: "8px 18px", borderRadius: 8, border: "none",
            background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`,
            color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600,
            opacity: loading || !firInput.trim() ? 0.5 : 1,
            transition: "all 0.15s",
          }}
        >
          {loading ? "Loading..." : "Visualize"}
        </button>
        {onClose && (
          <button onClick={onClose} style={{
            padding: "8px 10px", borderRadius: 8, border: `1px solid ${T.cardBorder}`,
            background: "transparent", color: T.textMuted, cursor: "pointer",
          }}>
            <X size={16} />
          </button>
        )}
        {firNumber && (
          <span style={{
            marginLeft: "auto", color: T.textMuted, fontSize: 11,
          }}>
            {stats ? `${stats.totalNodes} nodes · ${stats.totalEdges} edges` : ""}
          </span>
        )}
      </div>

      {/* ── Stats Bar ───────────────────────────────────────── */}
      {hasGraph && stats && (
        <div style={{
          display: "flex", gap: 8, flexWrap: "wrap",
        }}>
          {["FIR", "Accused", "Victim", "Evidence", "Location", "Transaction"].map((type) => {
            const count = stats.counts[type] || 0;
            if (count === 0) return null;
            const style = NODE_STYLES[type] || DEFAULT_STYLE;
            return (
              <span key={type} style={{
                padding: "3px 10px", borderRadius: 12, fontSize: 10, fontWeight: 600,
                background: style.bg, color: style.color,
                border: `1px solid ${style.border}44`,
              }}>
                {style.icon} {type} ×{count}
              </span>
            );
          })}
        </div>
      )}

      {/* ── Main Content ────────────────────────────────────── */}
      <div style={{
        display: "flex", gap: 16, flex: 1, minHeight: 0,
        flexDirection: selectedNode ? "row" : "column",
      }}>
        {/* Graph */}
        <div style={{
          flex: selectedNode ? 1.5 : 1,
          background: T.card, border: `1px solid ${T.cardBorder}`,
          borderRadius: 16, overflow: "hidden", position: "relative",
          minHeight: 450,
        }}>
          {!hasGraph && !loading && !error && (
            <div style={{
              position: "absolute", inset: 0,
              display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center",
              color: T.textMuted, fontSize: 14, gap: 12,
              zIndex: 1,
            }}>
              <div style={{ fontSize: 48 }}>🕸</div>
              <div>Enter an FIR number and click Visualize</div>
            </div>
          )}

          {error && (
            <div style={{
              position: "absolute", inset: 0,
              display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center",
              zIndex: 1, gap: 8,
            }}>
              <AlertTriangle size={32} color={T.danger} />
              <div style={{ color: T.danger, fontSize: 14 }}>{error}</div>
            </div>
          )}

          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onInit={setReactFlowInstance}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-left"
            style={{ background: "#0D1320", height: "100%" }}
          >
            <Background color="#1E293B" gap={24} size={1} />
            <Controls
              showInteractive={false}
              style={{
                background: T.card,
                border: `1px solid ${T.cardBorder}`,
                borderRadius: 8,
                button: { background: T.card, color: T.textSecondary, border: "none" },
              }}
            />
            <MiniMap
              nodeColor={(node) => {
                const s = NODE_STYLES[node.data?.nodeType] || DEFAULT_STYLE;
                return s.color + "44";
              }}
              maskColor="#0D1320AA"
              style={{
                background: T.card,
                border: `1px solid ${T.cardBorder}`,
                borderRadius: 8,
              }}
            />
          </ReactFlow>
        </div>

        {/* Details Panel */}
        {selectedNode && (
          <div style={{
            flex: 1, maxWidth: 380, minWidth: 280,
            background: T.card, border: `1px solid ${T.cardBorder}`,
            borderRadius: 16, padding: 16, overflowY: "auto",
            animation: "slideUp 0.3s ease",
            maxHeight: 500,
          }}>
            <div style={{
              display: "flex", justifyContent: "space-between",
              alignItems: "flex-start", marginBottom: 12,
            }}>
              <div>
                <div style={{
                  fontSize: 11, fontWeight: 700, color: (NODE_STYLES[selectedNode.node.type] || DEFAULT_STYLE).color,
                  marginBottom: 4,
                }}>
                  {(NODE_STYLES[selectedNode.node.type] || DEFAULT_STYLE).icon} {selectedNode.node.type}
                </div>
                <div style={{ color: T.textPrimary, fontSize: 16, fontWeight: 600 }}>
                  {selectedNode.node.label}
                </div>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                style={{
                  padding: 4, borderRadius: 6, border: "none",
                  background: "transparent", color: T.textMuted, cursor: "pointer",
                }}
              >
                <X size={14} />
              </button>
            </div>

            {/* Metadata */}
            {selectedNode.node.metadata && Object.keys(selectedNode.node.metadata).length > 0 && (
              <div style={{ marginBottom: 16 }}>
                {Object.entries(selectedNode.node.metadata).map(([key, val]) => {
                  if (!val || val === "null" || val === "None" || val === "") return null;
                  return (
                    <div key={key} style={{
                      display: "flex", justifyContent: "space-between",
                      padding: "4px 0", borderBottom: `1px solid ${T.cardBorder}`,
                    }}>
                      <span style={{ color: T.textMuted, fontSize: 11, textTransform: "capitalize" }}>
                        {key.replace(/_/g, " ")}
                      </span>
                      <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 500, textAlign: "right", maxWidth: "60%" }}>
                        {String(val)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Risk for accused */}
            {selectedNode.node.type === "Accused" && selectedNode.node.metadata?.risk_score > 0 && (
              <div style={{
                padding: 10, borderRadius: 8, marginBottom: 16,
                background: selectedNode.node.metadata.risk_score >= 8
                  ? "rgba(220,38,38,0.15)" : selectedNode.node.metadata.risk_score >= 5
                    ? "rgba(234,88,12,0.15)" : "rgba(34,197,94,0.15)",
                border: `1px solid ${selectedNode.node.metadata.risk_score >= 8 ? "#DC262644" : selectedNode.node.metadata.risk_score >= 5 ? "#EA580C44" : "#22C55E44"}`,
                display: "flex", alignItems: "center", gap: 8,
              }}>
                <AlertTriangle size={16} color={selectedNode.node.metadata.risk_score >= 8 ? "#DC2626" : selectedNode.node.metadata.risk_score >= 5 ? "#EA580C" : "#22C55E"} />
                <span style={{ fontSize: 12, fontWeight: 600, color: T.textPrimary }}>
                  Risk Score: {selectedNode.node.metadata.risk_score}/10
                </span>
              </div>
            )}

            {/* Connections */}
            <div style={{ fontSize: 11, fontWeight: 600, color: T.textMuted, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 8 }}>
              Connections ({selectedNode.edges.length})
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {selectedNode.edges.slice(0, 15).map((e, i) => {
                const neighborId = e.source === selectedNode.node.id ? e.target : e.source;
                const neighborNode = nodes.find((n) => n.id === neighborId);
                if (!neighborNode) return null;
                const ns = NODE_STYLES[neighborNode.data?.nodeType] || DEFAULT_STYLE;
                const es = EDGE_STYLES[e.label] || { color: "#94A3B8", label: e.label };
                return (
                  <div key={i} style={{
                    display: "flex", alignItems: "center", gap: 8,
                    padding: "6px 8px", background: T.inputBg, borderRadius: 8,
                  }}>
                    <div style={{
                      width: 6, height: 6, borderRadius: "50%", background: ns.color, flexShrink: 0,
                    }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ color: T.textPrimary, fontSize: 12, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {neighborNode.data?.label}
                      </div>
                      <div style={{ color: es.color, fontSize: 10 }}>
                        {es.label}
                      </div>
                    </div>
                  </div>
                );
              })}
              {selectedNode.edges.length > 15 && (
                <div style={{ color: T.textMuted, fontSize: 11, textAlign: "center", padding: 4 }}>
                  +{selectedNode.edges.length - 15} more connections
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ── Edge Legend ──────────────────────────────────────── */}
      {hasGraph && (
        <div style={{
          display: "flex", gap: 12, flexWrap: "wrap",
          padding: "10px 14px", background: T.card,
          border: `1px solid ${T.cardBorder}`, borderRadius: 10,
        }}>
          <span style={{ color: T.textMuted, fontSize: 10, fontWeight: 600 }}>Relationships:</span>
          {Object.values(EDGE_STYLES).map((es) => (
            <span key={es.label} style={{
              display: "flex", alignItems: "center", gap: 4,
              fontSize: 10, color: es.color, fontWeight: 500,
            }}>
              <span style={{ width: 16, height: 2, background: es.color, display: "inline-block" }} />
              <span>→</span>
              {es.label}
            </span>
          ))}
        </div>
      )}

      <style>{`
        @keyframes slideUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        .react-flow__node { cursor: pointer !important; }
        .react-flow__controls-button { background: ${T.card} !important; border: 1px solid ${T.cardBorder} !important; color: ${T.textSecondary} !important; }
        .react-flow__controls-button:hover { background: ${T.accentGlow} !important; }
        .react-flow__attribution { display: none !important; }
      `}</style>
    </div>
  );
}
