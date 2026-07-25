import { useState, useEffect, useCallback, useMemo } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Search, X, MapPin, SlidersHorizontal, RefreshCw } from "lucide-react";
import { getHotspotMap } from "../../services/hotspotService";
import { T } from "../../styles/theme";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const RISK = {
  High: { color: "#EF4444", fill: "rgba(239,68,68,0.3)", radius: 18, label: "High Risk" },
  Medium: { color: "#F59E0B", fill: "rgba(245,158,11,0.3)", radius: 14, label: "Medium Risk" },
  Low: { color: "#22C55E", fill: "rgba(34,197,94,0.3)", radius: 10, label: "Low Risk" },
};

function FitBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 0) {
      const bounds = L.latLngBounds(points.map((p) => [p.latitude, p.longitude]));
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
    }
  }, [points, map]);
  return null;
}

function clusterPoints(points, radius = 0.08) {
  const clusters = [];
  const assigned = new Set();
  points.forEach((p, i) => {
    if (assigned.has(i)) return;
    const group = [p];
    assigned.add(i);
    points.forEach((q, j) => {
      if (assigned.has(j)) return;
      if (Math.abs(p.latitude - q.latitude) < radius && Math.abs(p.longitude - q.longitude) < radius) {
        group.push(q);
        assigned.add(j);
      }
    });
    clusters.push(group);
  });
  return clusters.map((group) => {
    const avgLat = group.reduce((s, p) => s + p.latitude, 0) / group.length;
    const avgLng = group.reduce((s, p) => s + p.longitude, 0) / group.length;
    const totalCrimes = group.reduce((s, p) => s + p.crime_count, 0);
    const maxRisk = group.reduce((max, p) => (p.risk_score > max.risk_score ? p : max), group[0]);
    return { latitude: avgLat, longitude: avgLng, crime_count: totalCrimes, risk_score: maxRisk.risk_score, risk_level: maxRisk.risk_level, points: group, count: group.length };
  });
}

export default function CrimeHotspotMap({ initialDistrict, onClose }) {
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState(initialDistrict || "");
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  const loadMap = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getHotspotMap();
      let filtered = data?.points || [];
      if (search.trim()) {
        const q = search.toLowerCase();
        filtered = filtered.filter((p) => p.district?.toLowerCase().includes(q) || p.city?.toLowerCase().includes(q) || p.area?.toLowerCase().includes(q));
      }
      setPoints(filtered);
      if (filtered.length === 0 && search.trim()) setError(`No hotspots matching "${search}"`);
      else if (filtered.length === 0) setError("No hotspot data available");
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to load hotspot map");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { loadMap(); }, [loadMap]);

  const clusters = useMemo(() => clusterPoints(points), [points]);

  const stats = useMemo(() => {
    if (!points.length) return null;
    return {
      totalCrimes: points.reduce((s, p) => s + p.crime_count, 0),
      highRisk: points.filter((p) => p.risk_level === "High").length,
      mediumRisk: points.filter((p) => p.risk_level === "Medium").length,
      lowRisk: points.filter((p) => p.risk_level === "Low").length,
      districts: new Set(points.map((p) => p.district)).size,
      totalPoints: points.length,
    };
  }, [points]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, height: "100%", minHeight: 500 }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", padding: "12px 16px", background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 12 }}>
        <MapPin size={16} color={T.textMuted} />
        <div style={{ position: "relative", flex: 1, minWidth: 180, maxWidth: 320 }}>
          <Search size={14} color={T.textMuted} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)" }} />
          <input type="text" placeholder="Search district, city..." value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") loadMap(); }}
            style={{ width: "100%", padding: "8px 12px 8px 32px", borderRadius: 8, border: `1px solid ${T.cardBorder}`, background: T.inputBg, color: T.textPrimary, fontSize: 13, outline: "none", boxSizing: "border-box" }} />
        </div>
        <button onClick={() => setShowFilters(!showFilters)}
          style={{ padding: "8px 10px", borderRadius: 8, border: `1px solid ${showFilters ? T.accent + "44" : T.cardBorder}`, background: showFilters ? T.accentGlow : T.inputBg, color: showFilters ? T.accent : T.textSecondary, cursor: "pointer" }}>
          <SlidersHorizontal size={16} />
        </button>
        <button onClick={loadMap}
          style={{ padding: "8px 14px", borderRadius: 8, border: "none", background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`, color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
          <RefreshCw size={14} /> Refresh
        </button>
        {onClose && (
          <button onClick={onClose} style={{ padding: "8px 10px", borderRadius: 8, border: `1px solid ${T.cardBorder}`, background: "transparent", color: T.textMuted, cursor: "pointer" }}>
            <X size={16} />
          </button>
        )}
        {stats && <span style={{ marginLeft: "auto", color: T.textMuted, fontSize: 11 }}>{stats.districts} districts · {stats.totalPoints} locations · {stats.totalCrimes} crimes</span>}
      </div>

      {showFilters && (
        <div style={{ padding: "12px 16px", background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 12, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", animation: "slideUp 0.2s ease" }}>
          <Calendar size={16} color={T.textMuted} />
          <span style={{ color: T.textMuted, fontSize: 12 }}>Risk Legend:</span>
          <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: T.textMuted }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#EF4444" }} /> High ({stats?.highRisk || 0})
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: T.textMuted }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#F59E0B" }} /> Medium ({stats?.mediumRisk || 0})
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: T.textMuted }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#22C55E" }} /> Low ({stats?.lowRisk || 0})
          </span>
        </div>
      )}

      <div style={{ flex: 1, borderRadius: 16, overflow: "hidden", border: `1px solid ${T.cardBorder}`, position: "relative", minHeight: 450 }}>
        {loading && (
          <div style={{ position: "absolute", inset: 0, zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(13,19,32,0.7)" }}>
            <div style={{ color: T.textMuted, fontSize: 14 }}>Loading map...</div>
          </div>
        )}
        {error && !loading && points.length === 0 && (
          <div style={{ position: "absolute", inset: 0, zIndex: 1000, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8 }}>
            <div style={{ fontSize: 48 }}>🗺</div>
            <div style={{ color: T.danger, fontSize: 14 }}>{error}</div>
            <button onClick={loadMap} style={{ padding: "8px 20px", borderRadius: 8, border: "none", background: T.accent, color: "#fff", cursor: "pointer", fontSize: 13 }}>Retry</button>
          </div>
        )}
        <MapContainer center={[15.5, 76.5]} zoom={7} style={{ height: "100%", width: "100%" }} zoomControl={true}>
          <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {points.length > 0 && <FitBounds points={points} />}
          {clusters.map((c, idx) => {
            const r = RISK[c.risk_level] || RISK.Low;
            return (
              <CircleMarker key={`c-${idx}`} center={[c.latitude, c.longitude]} radius={r.radius}
                pathOptions={{ color: r.color, fillColor: r.fill, fillOpacity: 0.6, weight: 2, opacity: 0.8 }}
                eventHandlers={{ click: () => setSelectedPoint(c) }}>
                <Popup>
                  <div style={{ fontFamily: "Inter, sans-serif", minWidth: 170 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: r.color, marginBottom: 4 }}>{r.label} — {c.count} location{c.count > 1 ? "s" : ""}</div>
                    <div style={{ fontSize: 11, color: "#64748B", marginBottom: 4 }}>{c.crime_count} crimes · Score: {Math.round(c.risk_score)}</div>
                    {c.points.slice(0, 5).map((p, i) => (
                      <div key={i} style={{ fontSize: 10, color: "#94A3B8", padding: "1px 0" }}>• {p.district} — {p.crime_count} crimes</div>
                    ))}
                    {c.points.length > 5 && <div style={{ fontSize: 10, color: "#94A3B8" }}>+{c.points.length - 5} more</div>}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
          {points.filter((p) => !clusters.some((c) => c.points.length > 1 && c.points.includes(p))).map((p, idx) => {
            const r = RISK[p.risk_level] || RISK.Low;
            return (
              <CircleMarker key={`p-${idx}`} center={[p.latitude, p.longitude]} radius={r.radius}
                pathOptions={{ color: r.color, fillColor: r.fill, fillOpacity: 0.6, weight: 2, opacity: 0.8 }}
                eventHandlers={{ click: () => setSelectedPoint({ points: [p], count: 1, ...p }) }}>
                <Popup>
                  <div style={{ fontFamily: "Inter, sans-serif", minWidth: 160 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: r.color, marginBottom: 2 }}>{p.district}</div>
                    <div style={{ fontSize: 11, color: "#64748B", marginBottom: 4 }}>{p.city}{p.city && p.area ? " · " : ""}{p.area}</div>
                    <div style={{ display: "flex", gap: 12, marginTop: 6 }}>
                      <div style={{ textAlign: "center" }}><div style={{ fontSize: 16, fontWeight: 700, color: "#1E293B" }}>{p.crime_count}</div><div style={{ fontSize: 9, color: "#94A3B8" }}>Crimes</div></div>
                      <div style={{ textAlign: "center" }}><div style={{ fontSize: 16, fontWeight: 700, color: r.color }}>{Math.round(p.risk_score)}</div><div style={{ fontSize: 9, color: "#94A3B8" }}>Score</div></div>
                      <div style={{ textAlign: "center" }}><div style={{ fontSize: 12, fontWeight: 700, color: r.color, padding: "2px 8px", borderRadius: 10, background: r.color + "22" }}>{p.risk_level}</div><div style={{ fontSize: 9, color: "#94A3B8" }}>Level</div></div>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>

      {selectedPoint && (
        <div style={{ padding: "12px 16px", background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 12, display: "flex", alignItems: "center", gap: 12, animation: "slideUp 0.2s ease" }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: (RISK[selectedPoint.risk_level] || RISK.Low).color, flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <div style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>
              {selectedPoint.count > 1 ? `${selectedPoint.count} locations clustered` : selectedPoint.points[0]?.district || "Unknown"}
            </div>
            <div style={{ color: T.textMuted, fontSize: 11 }}>
              {selectedPoint.crime_count} crimes · Score: {Math.round(selectedPoint.risk_score)} · {selectedPoint.risk_level} Risk
            </div>
          </div>
          <button onClick={() => setSelectedPoint(null)} style={{ padding: 4, borderRadius: 6, border: "none", background: "transparent", color: T.textMuted, cursor: "pointer" }}><X size={14} /></button>
        </div>
      )}

      <style>{`
        @keyframes slideUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        .leaflet-container { background: #0D1320 !important; }
        .leaflet-popup-content-wrapper { border-radius: 12px !important; padding: 4px !important; }
        .leaflet-popup-content { margin: 8px 12px !important; }
        .leaflet-control-zoom a { background: #1E293B !important; color: #E2E8F0 !important; border-color: #334155 !important; }
        .leaflet-control-zoom a:hover { background: #334155 !important; }
      `}</style>
    </div>
  );
}
