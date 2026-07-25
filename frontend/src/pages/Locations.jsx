import { useState, useEffect, useCallback, useMemo } from "react";
import { T } from "../styles/theme";
import {
  listLocations, getLocation, createLocation, updateLocation, deleteLocation,
  getLocationUsage, getLocationStatistics,
} from "../services/locationsService";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";

// ═══════════════════════════════════════════════════════════════
// ANIMATIONS
// ═══════════════════════════════════════════════════════════════

const ANIM_STYLES = `
  @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
  @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
`;

const STYLE = {
  modalOverlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
    display: "flex", alignItems: "center", justifyContent: "center",
    zIndex: 1000, padding: 20,
  },
  modalContent: {
    background: T.card, border: `1px solid ${T.cardBorder}`,
    borderRadius: 16, width: "100%", maxWidth: 520,
    maxHeight: "90vh", overflow: "auto", animation: "slideUp 0.25s ease",
  },
  input: {
    width: "100%", padding: "10px 12px", borderRadius: 8,
    border: `1px solid ${T.inputBorder}`, background: T.inputBg,
    color: T.textPrimary, fontSize: 13, outline: "none", boxSizing: "border-box",
  },
  select: {
    width: "100%", padding: "10px 12px", borderRadius: 8,
    border: `1px solid ${T.inputBorder}`, background: T.inputBg,
    color: T.textPrimary, fontSize: 13, outline: "none", cursor: "pointer", boxSizing: "border-box",
  },
  label: { display: "block", color: T.textSecondary, fontSize: 11, fontWeight: 600, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.5px" },
  btnPrimary: {
    padding: "10px 20px", borderRadius: 8, border: "none",
    background: `linear-gradient(135deg, ${T.accent}, ${T.purple})`, color: "#fff",
    fontSize: 13, fontWeight: 600, cursor: "pointer",
  },
  btnSecondary: {
    padding: "10px 20px", borderRadius: 8, border: `1px solid ${T.cardBorder}`,
    background: T.inputBg, color: T.textSecondary, fontSize: 13, cursor: "pointer",
  },
  btnDanger: {
    padding: "10px 20px", borderRadius: 8, border: "none",
    background: T.danger, color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer",
  },
};

// ═══════════════════════════════════════════════════════════════
// KPI CARD
// ═══════════════════════════════════════════════════════════════

function KPICard({ icon, label, value, color = T.accent }) {
  return (
    <div style={{
      background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 14,
      padding: "14px 18px", display: "flex", alignItems: "center", gap: 12, minWidth: 120,
      transition: "all 0.2s",
    }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = `${color}33`; e.currentTarget.style.transform = "translateY(-1px)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = T.cardBorder; e.currentTarget.style.transform = "none"; }}
    >
      <div style={{ width: 38, height: 38, borderRadius: 10, background: `${color}18`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 }}>{icon}</div>
      <div style={{ minWidth: 0 }}>
        <div style={{ color: T.textSecondary, fontSize: 10, fontWeight: 500, marginBottom: 1 }}>{label}</div>
        <div style={{ color: T.textPrimary, fontSize: 20, fontWeight: 700 }}>{value}</div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// LOCATION FORM MODAL
// ═══════════════════════════════════════════════════════════════

function LocationFormModal({ location, onClose, onSaved }) {
  const isEdit = !!location;
  const [form, setForm] = useState({
    district: location?.district || "",
    city: location?.city || "",
    area: location?.area || "",
    pincode: location?.pincode || "",
    latitude: location?.latitude?.toString() || "",
    longitude: location?.longitude?.toString() || "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.district.trim() || !form.city.trim() || !form.area.trim()) {
      setError("District, city, and area are required");
      return;
    }
    // Validate lat/lng
    const lat = form.latitude ? parseFloat(form.latitude) : null;
    const lng = form.longitude ? parseFloat(form.longitude) : null;
    if (lat !== null && (lat < -90 || lat > 90)) { setError("Latitude must be between -90 and 90"); return; }
    if (lng !== null && (lng < -180 || lng > 180)) { setError("Longitude must be between -180 and 180"); return; }

    setSaving(true);
    setError("");
    try {
      const payload = {
        district: form.district.trim(),
        city: form.city.trim(),
        area: form.area.trim(),
        pincode: form.pincode.trim() || null,
        latitude: lat,
        longitude: lng,
      };
      if (isEdit) await updateLocation(location.location_id, payload);
      else await createLocation(payload);
      onSaved();
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to save location");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={STYLE.modalOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={STYLE.modalContent}>
        <div style={{ padding: "20px 24px", borderBottom: `1px solid ${T.cardBorder}` }}>
          <h2 style={{ color: T.textPrimary, fontSize: 18, fontWeight: 700, margin: 0 }}>{isEdit ? "Edit Location" : "Add Location"}</h2>
          <p style={{ color: T.textMuted, fontSize: 12, margin: "4px 0 0" }}>{isEdit ? "Update location details" : "Register a new geographic location"}</p>
        </div>
        <form onSubmit={handleSubmit} style={{ padding: 24, display: "flex", flexDirection: "column", gap: 14 }}>
          {error && (
            <div style={{ padding: "10px 14px", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 8, color: T.danger, fontSize: 13 }}>{error}</div>
          )}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={STYLE.label}>District *</label>
              <input style={STYLE.input} value={form.district} onChange={(e) => handleChange("district", e.target.value)} placeholder="e.g. Bengaluru Urban" required />
            </div>
            <div>
              <label style={STYLE.label}>City *</label>
              <input style={STYLE.input} value={form.city} onChange={(e) => handleChange("city", e.target.value)} placeholder="e.g. Bengaluru" required />
            </div>
          </div>
          <div>
            <label style={STYLE.label}>Area / Locality *</label>
            <input style={STYLE.input} value={form.area} onChange={(e) => handleChange("area", e.target.value)} placeholder="e.g. Whitefield, MG Road" required />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            <div>
              <label style={STYLE.label}>Pincode</label>
              <input style={STYLE.input} value={form.pincode} onChange={(e) => handleChange("pincode", e.target.value)} placeholder="e.g. 560001" maxLength={10} />
            </div>
            <div>
              <label style={STYLE.label}>Latitude</label>
              <input style={STYLE.input} type="number" step="any" value={form.latitude} onChange={(e) => handleChange("latitude", e.target.value)} placeholder="-90 to 90" />
            </div>
            <div>
              <label style={STYLE.label}>Longitude</label>
              <input style={STYLE.input} type="number" step="any" value={form.longitude} onChange={(e) => handleChange("longitude", e.target.value)} placeholder="-180 to 180" />
            </div>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
            <button type="button" onClick={onClose} style={STYLE.btnSecondary}>Cancel</button>
            <button type="submit" disabled={saving} style={{ ...STYLE.btnPrimary, opacity: saving ? 0.6 : 1, cursor: saving ? "not-allowed" : "pointer" }}>
              {saving ? "Saving..." : isEdit ? "Update Location" : "Add Location"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// CONFIRM MODAL
// ═══════════════════════════════════════════════════════════════

function ConfirmModal({ title, message, confirmText = "Delete", confirmColor = T.danger, onConfirm, onClose }) {
  return (
    <div style={STYLE.modalOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={{ ...STYLE.modalContent, maxWidth: 400 }}>
        <div style={{ padding: "24px", textAlign: "center" }}>
          <span style={{ fontSize: 40 }}>⚠️</span>
          <h3 style={{ color: T.textPrimary, fontSize: 16, margin: "12px 0 4px" }}>{title}</h3>
          <p style={{ color: T.textMuted, fontSize: 13, margin: 0, lineHeight: 1.5 }}>{message}</p>
          <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 20 }}>
            <button onClick={onClose} style={STYLE.btnSecondary}>Cancel</button>
            <button onClick={onConfirm} style={{ ...STYLE.btnDanger, background: confirmColor }}>{confirmText}</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAP EMBED
// ═══════════════════════════════════════════════════════════════

function LocationMap({ lat, lng, name }) {
  if (lat == null || lng == null) {
    return (
      <div style={{ padding: "20px", textAlign: "center", borderRadius: 10, background: T.inputBg }}>
        <span style={{ fontSize: 24 }}>🗺️</span>
        <p style={{ color: T.textMuted, fontSize: 12, margin: "8px 0 0" }}>Map unavailable — add coordinates to enable map view</p>
      </div>
    );
  }
  const bbox = `${lng - 0.01},${lat - 0.01},${lng + 0.01},${lat + 0.01}`;
  const src = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lng}`;
  return (
    <div style={{ borderRadius: 10, overflow: "hidden", border: `1px solid ${T.cardBorder}` }}>
      <iframe
        title={`Map of ${name}`}
        src={src}
        width="100%"
        height="200"
        style={{ border: "none", display: "block" }}
        loading="lazy"
      />
      <div style={{ padding: "6px 10px", background: T.inputBg, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ color: T.textMuted, fontSize: 10 }}>OpenStreetMap</span>
        <a href={`https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}`} target="_blank" rel="noopener noreferrer"
          style={{ color: T.accent, fontSize: 10, textDecoration: "none" }}>Open in Maps →</a>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// USAGE STATS
// ═══════════════════════════════════════════════════════════════

function UsageStats({ usage }) {
  if (!usage) return null;
  const items = [
    { icon: "📋", label: "FIRs", value: usage.fir_count, color: T.accent },
    { icon: "🔬", label: "Evidence", value: usage.evidence_count, color: T.success },
    { icon: "👤", label: "Accused", value: usage.accused_count, color: T.warning },
    { icon: "👥", label: "Victims", value: usage.victim_count, color: T.purple },
  ];
  const hasData = items.some((i) => i.value > 0);
  return (
    <div>
      <div style={{ color: T.textMuted, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 10 }}>Cross-Module Usage</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        {items.map((item, i) => (
          <div key={i} style={{
            padding: "10px", borderRadius: 8, textAlign: "center",
            background: `${item.color}08`, border: `1px solid ${item.color}15`,
          }}>
            <div style={{ fontSize: 18, marginBottom: 2 }}>{item.icon}</div>
            <div style={{ color: T.textPrimary, fontSize: 18, fontWeight: 700 }}>
              {hasData ? item.value : "—"}
            </div>
            <div style={{ color: T.textMuted, fontSize: 10 }}>{item.label}</div>
          </div>
        ))}
      </div>
      {!hasData && (
        <p style={{ color: T.textMuted, fontSize: 11, textAlign: "center", margin: "8px 0 0" }}>
          No linked records yet — usage stats update when FIRs reference this location
        </p>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// LOCATION DETAIL DRAWER
// ═══════════════════════════════════════════════════════════════

function LocationDrawer({ loc, onClose, onEdit, onDelete }) {
  const [usage, setUsage] = useState(null);
  const [usageLoading, setUsageLoading] = useState(false);

  useEffect(() => {
    if (!loc) return;
    setUsageLoading(true);
    setUsage(null);
    getLocationUsage(loc.location_id)
      .then(setUsage)
      .catch(() => setUsage(null))
      .finally(() => setUsageLoading(false));
  }, [loc?.location_id]);

  if (!loc) return null;
  const hasCoords = loc.latitude != null && loc.longitude != null;

  return (
    <div style={STYLE.modalOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={{ ...STYLE.modalContent, maxWidth: 480 }}>
        {/* Header */}
        <div style={{ padding: "24px", textAlign: "center", borderBottom: `1px solid ${T.cardBorder}` }}>
          <div style={{ width: 56, height: 56, borderRadius: 14, background: `${T.accent}18`, display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 24, color: T.accent, marginBottom: 12 }}>📍</div>
          <h2 style={{ color: T.textPrimary, fontSize: 18, fontWeight: 700, margin: "0 0 4px" }}>{loc.area}</h2>
          <p style={{ color: T.textMuted, fontSize: 13, margin: 0 }}>{loc.city}, {loc.district}</p>
          {loc.pincode && <p style={{ color: T.textMuted, fontSize: 11, margin: "2px 0 0" }}>PIN: {loc.pincode}</p>}
        </div>

        {/* Map */}
        <div style={{ padding: "16px 24px" }}>
          <LocationMap lat={loc.latitude} lng={loc.longitude} name={`${loc.area}, ${loc.city}`} />
        </div>

        {/* Details */}
        <div style={{ padding: "0 24px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ color: T.textMuted, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" }}>Location Details</div>
          {[
            { label: "District", value: loc.district },
            { label: "City", value: loc.city },
            { label: "Area", value: loc.area },
            { label: "Pincode", value: loc.pincode || "—" },
            { label: "Latitude", value: loc.latitude != null ? loc.latitude.toFixed(6) : "—" },
            { label: "Longitude", value: loc.longitude != null ? loc.longitude.toFixed(6) : "—" },
            { label: "Created", value: loc.created_at ? new Date(loc.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric" }) : "—" },
          ].map((item, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: i < 6 ? `1px solid ${T.cardBorder}` : "none" }}>
              <span style={{ color: T.textMuted, fontSize: 12 }}>{item.label}</span>
              <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 500 }}>{item.value}</span>
            </div>
          ))}
        </div>

        {/* Usage Stats */}
        <div style={{ padding: "0 24px 16px" }}>
          {usageLoading ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {[1, 2, 3, 4].map((i) => (
                <div key={i} style={{ padding: 10, borderRadius: 8, background: T.inputBg }}>
                  <div style={{ height: 18, width: "50%", margin: "0 auto", background: T.cardBorder, borderRadius: 4, animation: "shimmer 1.5s ease-in-out infinite" }} />
                </div>
              ))}
            </div>
          ) : (
            <UsageStats usage={usage} />
          )}
        </div>

        {/* Actions */}
        <div style={{ padding: "16px 24px", borderTop: `1px solid ${T.cardBorder}`, display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button onClick={() => { onEdit(loc); onClose(); }} style={STYLE.btnPrimary}>Edit</button>
          <button onClick={() => { onDelete(loc); onClose(); }} style={STYLE.btnDanger}>Delete</button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════

export default function Locations({ user }) {
  const canCreate = user?.role_id <= 2; // Admin or Investigator
  const canDelete = user?.role_id === 1; // Admin only
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [districtFilter, setDistrictFilter] = useState("");
  const [cityFilter, setCityFilter] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Statistics data
  const [statsData, setStatsData] = useState(null);

  // Modals
  const [showFormModal, setShowFormModal] = useState(false);
  const [editLocation, setEditLocation] = useState(null);
  const [selectedLoc, setSelectedLoc] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  // Compute stats
  const stats = useMemo(() => {
    const uniqueDistricts = new Set(locations.map((l) => l.district)).size;
    const uniqueCities = new Set(locations.map((l) => l.city)).size;
    return { total: total, districts: uniqueDistricts, cities: uniqueCities };
  }, [locations, total]);

  const fetchLocations = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = { page, page_size: 20 };
      if (search) params.search = search;
      if (districtFilter) params.district = districtFilter;
      if (cityFilter) params.city = cityFilter;
      const data = await listLocations(params);
      setLocations(data.items || []);
      setTotalPages(data.total_pages || 1);
      setTotal(data.total || 0);
    } catch (err) {
      if (err?.response?.status === 422) {
        setError("Data format error. The API response doesn't match expected schema.");
      } else {
        setError(err?.response?.data?.detail || "Failed to load locations");
      }
    } finally {
      setLoading(false);
    }
  }, [search, districtFilter, cityFilter, page]);

  useEffect(() => { fetchLocations(); }, [fetchLocations]);

  const fetchStats = useCallback(async () => {
    try {
      const data = await getLocationStatistics();
      setStatsData(data);
    } catch { /* stats are non-critical */ }
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  // ── Export CSV ──
  const exportCSV = () => {
    let csv = "District,City,Area,Pincode,Latitude,Longitude,Created\n";
    locations.forEach((l) => {
      csv += `"${l.district}","${l.city}","${l.area}","${l.pincode || ""}",${l.latitude ?? ""},${l.longitude ?? ""},"${l.created_at?.split("T")[0] || ""}"\n`;
    });
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `locations-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click(); URL.revokeObjectURL(url);
    showToast("CSV exported successfully");
  };

  // ── Delete handler ──
  const handleDelete = (loc) => {
    setConfirmAction({
      title: "Delete Location",
      message: `Are you sure you want to delete "${loc.area || loc.city}"? ${loc.fir_count > 0 ? "This location is linked to FIR records." : ""}`,
      onConfirm: async () => {
        try {
          await deleteLocation(loc.location_id);
          showToast("Location deleted successfully");
          fetchLocations();
        } catch (err) {
          showToast(err?.response?.data?.detail || "Failed to delete location", "error");
        }
        setConfirmAction(null);
      },
    });
  };

  const pages = [];
  for (let i = 1; i <= totalPages; i++) pages.push(i);

  return (
    <PageShell title="Locations" user={user}>
      <style>{ANIM_STYLES}</style>

      {/* ── Toast ── */}
      {toast && (
        <div style={{
          position: "fixed", top: 20, right: 20, zIndex: 2000,
          padding: "12px 20px", borderRadius: 10,
          background: toast.type === "success" ? T.success : T.danger,
          color: "#fff", fontSize: 13, fontWeight: 600,
          boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
          animation: "slideUp 0.25s ease",
          display: "flex", alignItems: "center", gap: 8,
        }}>
          <span>{toast.type === "success" ? "✅" : "⚠️"}</span>
          {toast.message}
        </div>
      )}

      {/* ── Modals ── */}
      {showFormModal && (
        <LocationFormModal
          location={editLocation}
          onClose={() => { setShowFormModal(false); setEditLocation(null); }}
          onSaved={() => { showToast(editLocation ? "Location updated" : "Location added"); fetchLocations(); }}
        />
      )}
      {selectedLoc && (
        <LocationDrawer
          loc={selectedLoc}
          onClose={() => setSelectedLoc(null)}
          onEdit={(l) => { setEditLocation(l); setShowFormModal(true); }}
          onDelete={(l) => { setSelectedLoc(null); handleDelete(l); }}
        />
      )}
      {confirmAction && (
        <ConfirmModal
          title={confirmAction.title}
          message={confirmAction.message}
          onConfirm={confirmAction.onConfirm}
          onClose={() => setConfirmAction(null)}
        />
      )}

      {/* ── Statistics Section ── */}
      {statsData && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16, marginBottom: 20 }}>
          {/* Locations by District */}
          <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 14, padding: 18 }}>
            <h4 style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600, margin: "0 0 12px" }}>🏛️ Locations by District</h4>
            {(statsData.by_district || []).slice(0, 8).map((d, i) => {
              const pct = statsData.total_locations > 0 ? (d.count / statsData.total_locations) * 100 : 0;
              return (
                <div key={i} style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ color: T.textSecondary, fontSize: 12 }}>{d.district}</span>
                    <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>{d.count}</span>
                  </div>
                  <div style={{ background: T.inputBorder, borderRadius: 4, height: 6, overflow: "hidden" }}>
                    <div style={{ width: `${pct}%`, height: "100%", borderRadius: 4, background: `linear-gradient(90deg, ${T.accent}, ${T.purple})`, transition: "width 0.8s ease" }} />
                  </div>
                </div>
              );
            })}
            {(!statsData.by_district || statsData.by_district.length === 0) && (
              <p style={{ color: T.textMuted, fontSize: 12, textAlign: "center", padding: 20 }}>No district data</p>
            )}
          </div>

          {/* Locations by City */}
          <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 14, padding: 18 }}>
            <h4 style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600, margin: "0 0 12px" }}>🏙️ Locations by City</h4>
            {(statsData.by_city || []).slice(0, 8).map((c, i) => {
              const pct = statsData.total_locations > 0 ? (c.count / statsData.total_locations) * 100 : 0;
              return (
                <div key={i} style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ color: T.textSecondary, fontSize: 12 }}>{c.city}</span>
                    <span style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>{c.count}</span>
                  </div>
                  <div style={{ background: T.inputBorder, borderRadius: 4, height: 6, overflow: "hidden" }}>
                    <div style={{ width: `${pct}%`, height: "100%", borderRadius: 4, background: `linear-gradient(90deg, ${T.success}, ${T.accent})`, transition: "width 0.8s ease" }} />
                  </div>
                </div>
              );
            })}
            {(!statsData.by_city || statsData.by_city.length === 0) && (
              <p style={{ color: T.textMuted, fontSize: 12, textAlign: "center", padding: 20 }}>No city data</p>
            )}
          </div>

          {/* Newest Locations */}
          <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 14, padding: 18 }}>
            <h4 style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600, margin: "0 0 12px" }}>🆕 Newest Locations</h4>
            {(statsData.newest || []).map((n, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "8px 0", borderBottom: i < statsData.newest.length - 1 ? `1px solid ${T.cardBorder}` : "none",
              }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: `${T.accent}12`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, flexShrink: 0 }}>📍</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{n.area}</div>
                  <div style={{ color: T.textMuted, fontSize: 10 }}>{n.city}, {n.district}</div>
                </div>
                <span style={{ color: T.textMuted, fontSize: 10, whiteSpace: "nowrap" }}>
                  {n.created_at ? new Date(n.created_at).toLocaleDateString("en-IN", { month: "short", day: "numeric" }) : ""}
                </span>
              </div>
            ))}
            {(!statsData.newest || statsData.newest.length === 0) && (
              <p style={{ color: T.textMuted, fontSize: 12, textAlign: "center", padding: 20 }}>No locations yet</p>
            )}
          </div>
        </div>
      )}

      {/* ── Header ── */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: "0 0 4px" }}>Location Management</h1>
        <p style={{ color: T.textSecondary, fontSize: 13, margin: 0 }}>Manage geographic locations for crime reporting and analysis · Karnataka Police</p>
      </div>

      {/* ── KPI Cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 12, marginBottom: 20 }}>
        {[
          { icon: "📍", label: "Total Locations", value: stats.total, color: T.accent },
          { icon: "🏛️", label: "Districts Covered", value: stats.districts, color: T.success },
          { icon: "🏙️", label: "Cities Covered", value: stats.cities, color: T.purple },
        ].map((k, i) => <KPICard key={i} {...k} />)}
      </div>

      {/* ── Toolbar ── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ position: "relative", flex: 1, minWidth: 180, maxWidth: 280 }}>
          <span style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: T.textMuted, fontSize: 14, pointerEvents: "none" }}>🔍</span>
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search district, city, area..."
            style={{ width: "100%", padding: "8px 12px 8px 32px", borderRadius: 8, border: `1px solid ${T.inputBorder}`, background: T.inputBg, color: T.textPrimary, fontSize: 13, outline: "none", boxSizing: "border-box" }}
          />
        </div>
        <input value={districtFilter} onChange={(e) => { setDistrictFilter(e.target.value); setPage(1); }} placeholder="Filter district..." style={{ width: 140, padding: "8px 12px", borderRadius: 8, border: `1px solid ${T.inputBorder}`, background: T.inputBg, color: T.textPrimary, fontSize: 13, outline: "none" }} />
        <input value={cityFilter} onChange={(e) => { setCityFilter(e.target.value); setPage(1); }} placeholder="Filter city..." style={{ width: 140, padding: "8px 12px", borderRadius: 8, border: `1px solid ${T.inputBorder}`, background: T.inputBg, color: T.textPrimary, fontSize: 13, outline: "none" }} />
        <button onClick={exportCSV} style={{ ...STYLE.btnSecondary, whiteSpace: "nowrap" }}>📥 CSV</button>
        <button onClick={() => fetchLocations()} style={{ ...STYLE.btnSecondary, whiteSpace: "nowrap" }}>🔄 Refresh</button>
        {canCreate && (
          <button onClick={() => { setEditLocation(null); setShowFormModal(true); }} style={{ ...STYLE.btnPrimary, marginLeft: "auto" }}>+ Add Location</button>
        )}
      </div>

      {/* ── Table ── */}
      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 30 }}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} style={{ display: "flex", gap: 12, padding: "14px 20px", borderBottom: i < 4 ? `1px solid ${T.cardBorder}` : "none" }}>
                <div style={{ flex: 1, height: 14, borderRadius: 4, background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`, backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite" }} />
                <div style={{ flex: 1, height: 14, borderRadius: 4, background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`, backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite", animationDelay: "0.1s" }} />
                <div style={{ flex: 1, height: 14, borderRadius: 4, background: `linear-gradient(90deg, ${T.inputBg} 25%, ${T.cardBorder} 50%, ${T.inputBg} 75%)`, backgroundSize: "200% 100%", animation: "shimmer 1.5s ease-in-out infinite", animationDelay: "0.2s" }} />
                <div style={{ width: 80, height: 14, borderRadius: 4, background: T.inputBg }} />
              </div>
            ))}
          </div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <span style={{ fontSize: 32 }}>⚠️</span>
            <p style={{ color: T.danger, fontSize: 14, margin: "8px 0" }}>{error}</p>
            <button onClick={fetchLocations} style={{ padding: "6px 16px", borderRadius: 8, border: `1px solid ${T.cardBorder}`, background: T.inputBg, color: T.accent, fontSize: 12, cursor: "pointer" }}>Retry</button>
          </div>
        ) : locations.length === 0 ? (
          <div style={{ padding: 60, textAlign: "center" }}>
            <span style={{ fontSize: 40, opacity: 0.4 }}>📍</span>
            <p style={{ color: T.textMuted, fontSize: 14, margin: "12px 0 4px" }}>No locations found</p>
            <p style={{ color: T.textMuted, fontSize: 12, marginBottom: 16 }}>Add your first location to begin managing crime locations.</p>
            {canCreate && <button onClick={() => { setEditLocation(null); setShowFormModal(true); }} style={STYLE.btnPrimary}>+ Add Location</button>}
          </div>
        ) : (
          <>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                    {["District", "City", "Area", "Pincode", "Latitude", "Longitude", "Created", "Actions"].map((h) => (
                      <th key={h} style={{ color: T.textMuted, fontSize: 10, fontWeight: 600, textAlign: "left", padding: "14px 16px", textTransform: "uppercase", letterSpacing: "0.5px", whiteSpace: "nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {locations.map((l, i) => (
                    <tr key={l.location_id} style={{ borderBottom: i < locations.length - 1 ? `1px solid ${T.cardBorder}` : "none", transition: "background 0.1s", cursor: "pointer" }}
                      onMouseEnter={(e) => e.currentTarget.style.background = `${T.accent}06`}
                      onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                      onClick={() => setSelectedLoc(l)}
                    >
                      <td style={{ padding: "12px 16px", color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>{l.district}</td>
                      <td style={{ padding: "12px 16px", color: T.textSecondary, fontSize: 12 }}>{l.city}</td>
                      <td style={{ padding: "12px 16px", color: T.textSecondary, fontSize: 12 }}>{l.area}</td>
                      <td style={{ padding: "12px 16px", color: T.textSecondary, fontSize: 12 }}>{l.pincode || "—"}</td>
                      <td style={{ padding: "12px 16px", color: T.textMuted, fontSize: 11 }}>{l.latitude != null ? l.latitude.toFixed(4) : "—"}</td>
                      <td style={{ padding: "12px 16px", color: T.textMuted, fontSize: 11 }}>{l.longitude != null ? l.longitude.toFixed(4) : "—"}</td>
                      <td style={{ padding: "12px 16px", color: T.textSecondary, fontSize: 12, whiteSpace: "nowrap" }}>{l.created_at ? l.created_at.split("T")[0] : "—"}</td>
                      <td style={{ padding: "12px 16px" }} onClick={(e) => e.stopPropagation()}>
                        <div style={{ display: "flex", gap: 4 }}>
                          <button onClick={() => { setEditLocation(l); setShowFormModal(true); }} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: `${T.accent}15`, color: T.accent, fontSize: 11, cursor: "pointer" }}>Edit</button>
                          {canDelete && (
                            <button onClick={() => handleDelete(l)} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: `${T.danger}15`, color: T.danger, fontSize: 11, cursor: "pointer" }}>Del</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* ── Pagination ── */}
            {totalPages > 1 && (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 20px", borderTop: `1px solid ${T.cardBorder}` }}>
                <span style={{ color: T.textMuted, fontSize: 12 }}>{total} locations total</span>
                <div style={{ display: "flex", gap: 4 }}>
                  <button disabled={page <= 1} onClick={() => setPage(page - 1)} style={{ padding: "4px 10px", borderRadius: 6, border: `1px solid ${T.cardBorder}`, background: T.inputBg, color: page <= 1 ? T.textMuted : T.textPrimary, fontSize: 12, cursor: page <= 1 ? "default" : "pointer" }}>Prev</button>
                  {pages.slice(Math.max(0, page - 3), Math.min(totalPages, page + 2)).map((p) => (
                    <button key={p} onClick={() => setPage(p)} style={{ padding: "4px 10px", borderRadius: 6, border: "none", background: p === page ? T.accent : "transparent", color: p === page ? "#fff" : T.textSecondary, fontSize: 12, cursor: "pointer", fontWeight: p === page ? 600 : 400, minWidth: 28 }}>{p}</button>
                  ))}
                  <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} style={{ padding: "4px 10px", borderRadius: 6, border: `1px solid ${T.cardBorder}`, background: T.inputBg, color: page >= totalPages ? T.textMuted : T.textPrimary, fontSize: 12, cursor: page >= totalPages ? "default" : "pointer" }}>Next</button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </PageShell>
  );
}
