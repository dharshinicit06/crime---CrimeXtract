import { useState } from "react";
import { T } from "../styles/theme";
import { predictML } from "../services/predictionService";
import PageShell from "../components/PageShell";
import Button from "../components/Button";

const DISTRICTS = [
  "Bengaluru North", "Bengaluru South", "Mysuru",
  "Hubballi-Dharwad", "Mangaluru", "Belagavi",
  "Kalaburagi", "Shivamogga",
];

const CRIME_TYPES = [
  "Murder", "Robbery", "Burglary", "Assault",
  "Kidnapping", "Riot", "Fraud", "Cyber Crime",
];

const initialState = {
  state: "Karnataka",
  district: "",
  year: new Date().getFullYear(),
  crime_type: "",
  chargesheeted: "",
  convictions: "",
  population: "",
};

export default function AIPrediction({ user }) {
  const [form, setForm] = useState(initialState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});

  const set = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setFieldErrors((prev) => ({ ...prev, [field]: "" }));
    setError("");
    setResult(null);
  };

  const validate = () => {
    const errors = {};
    if (!form.district.trim()) errors.district = "District is required";
    if (!form.crime_type.trim()) errors.crime_type = "Crime type is required";

    const year = Number(form.year);
    if (!form.year) errors.year = "Year is required";
    else if (!Number.isInteger(year) || year < 2000 || year > 2100)
      errors.year = "Year must be between 2000 and 2100";

    const ch = Number(form.chargesheeted);
    if (!form.chargesheeted) errors.chargesheeted = "Required";
    else if (!Number.isInteger(ch) || ch < 0) errors.chargesheeted = "Must be a non-negative integer";

    const co = Number(form.convictions);
    if (!form.convictions) errors.convictions = "Required";
    else if (!Number.isInteger(co) || co < 0) errors.convictions = "Must be a non-negative integer";
    else if (ch > 0 && co > ch) errors.convictions = "Cannot exceed chargesheeted";

    const pop = Number(form.population);
    if (!form.population) errors.population = "Required";
    else if (!Number.isInteger(pop) || pop < 1) errors.population = "Must be a positive integer";

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handlePredict = async () => {
    if (!validate()) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await predictML({
        state: form.state,
        district: form.district,
        year: Number(form.year),
        crime_type: form.crime_type,
        chargesheeted: Number(form.chargesheeted),
        convictions: Number(form.convictions),
        population: Number(form.population),
      });
      setResult(data);
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail || err.message || "Prediction failed";

      if (status === 400) {
        setError(`Invalid input: ${detail}`);
      } else if (status === 422) {
        const msgs = err.response?.data?.detail;
        if (Array.isArray(msgs)) {
          setError(msgs.map((m) => m.msg).join("; "));
        } else if (typeof msgs === "string") {
          setError(msgs);
        } else {
          setError("Validation error. Please check your inputs.");
        }
      } else if (status === 503) {
        setError("ML model is not available. Please contact the administrator.");
      } else {
        setError(detail);
      }
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: "100%",
    padding: "12px 14px",
    background: T.inputBg,
    border: `1px solid ${T.inputBorder}`,
    borderRadius: 10,
    color: T.textPrimary,
    fontSize: 14,
    outline: "none",
    boxSizing: "border-box",
    transition: "border 0.2s",
  };

  const selectStyle = {
    ...inputStyle,
    appearance: "none",
    cursor: "pointer",
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2394a3b8' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
    backgroundRepeat: "no-repeat",
    backgroundPosition: "right 12px center",
    paddingRight: 36,
  };

  const fieldRow = {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 16,
  };

  const labelStyle = {
    display: "block",
    fontSize: 13,
    color: T.textSecondary,
    marginBottom: 6,
    fontWeight: 500,
  };

  return (
    <PageShell title="AI Prediction" user={user}>
      <div style={{ maxWidth: 680, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ color: T.textPrimary, fontSize: 24, fontWeight: 700, margin: 0 }}>
            Crime Prediction
          </h1>
          <p style={{ color: T.textMuted, fontSize: 14, margin: "6px 0 0" }}>
            Enter case attributes to predict the expected number of crime cases using the trained ML model.
          </p>
        </div>

        {/* Results card (when available) */}
        {result && (
          <div
            style={{
              background: "linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.08))",
              border: `1px solid ${T.accentGlow}`,
              borderRadius: 16,
              padding: 32,
              marginBottom: 28,
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 13, color: T.textMuted, marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>
              Predicted Cases
            </div>
            <div style={{ fontSize: 56, fontWeight: 800, color: T.accent, lineHeight: 1.1 }}>
              {result.predicted_cases.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
            <div style={{ color: T.textSecondary, fontSize: 13, marginTop: 8 }}>
              {form.district} · {form.crime_type} · {form.year}
            </div>
            <Button
              variant="secondary"
              onClick={() => { setResult(null); setForm(initialState); }}
              style={{ marginTop: 16 }}
            >
              Clear & Predict Again
            </Button>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div
            style={{
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.25)",
              borderRadius: 12,
              padding: "14px 18px",
              marginBottom: 20,
              color: T.danger,
              fontSize: 14,
            }}
          >
            {error}
          </div>
        )}

        {/* Prediction Form */}
        <div
          style={{
            background: T.card,
            border: `1px solid ${T.cardBorder}`,
            borderRadius: 16,
            padding: 28,
          }}
        >
          {/* State (readonly) + District */}
          <div style={fieldRow}>
            <div>
              <label style={labelStyle}>State</label>
              <input style={{ ...inputStyle, opacity: 0.6, cursor: "not-allowed" }} value={form.state} disabled />
            </div>
            <div>
              <label style={labelStyle}>District *</label>
              <select
                style={selectStyle}
                value={form.district}
                onChange={set("district")}
              >
                <option value="">Select district</option>
                {DISTRICTS.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
              {fieldErrors.district && (
                <div style={{ color: T.danger, fontSize: 12, marginTop: 4 }}>{fieldErrors.district}</div>
              )}
            </div>
          </div>

          {/* Year + Crime Type */}
          <div style={fieldRow}>
            <div>
              <label style={labelStyle}>Year *</label>
              <input
                type="number"
                style={{ ...inputStyle, borderColor: fieldErrors.year ? T.danger : T.inputBorder }}
                value={form.year}
                onChange={set("year")}
                min={2000}
                max={2100}
              />
              {fieldErrors.year && (
                <div style={{ color: T.danger, fontSize: 12, marginTop: 4 }}>{fieldErrors.year}</div>
              )}
            </div>
            <div>
              <label style={labelStyle}>Crime Type *</label>
              <select
                style={selectStyle}
                value={form.crime_type}
                onChange={set("crime_type")}
              >
                <option value="">Select type</option>
                {CRIME_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
              {fieldErrors.crime_type && (
                <div style={{ color: T.danger, fontSize: 12, marginTop: 4 }}>{fieldErrors.crime_type}</div>
              )}
            </div>
          </div>

          {/* Chargesheeted + Convictions */}
          <div style={fieldRow}>
            <div>
              <label style={labelStyle}>Chargesheeted Cases *</label>
              <input
                type="number"
                style={{ ...inputStyle, borderColor: fieldErrors.chargesheeted ? T.danger : T.inputBorder }}
                value={form.chargesheeted}
                onChange={set("chargesheeted")}
                min={0}
              />
              {fieldErrors.chargesheeted && (
                <div style={{ color: T.danger, fontSize: 12, marginTop: 4 }}>{fieldErrors.chargesheeted}</div>
              )}
            </div>
            <div>
              <label style={labelStyle}>Convictions *</label>
              <input
                type="number"
                style={{ ...inputStyle, borderColor: fieldErrors.convictions ? T.danger : T.inputBorder }}
                value={form.convictions}
                onChange={set("convictions")}
                min={0}
              />
              {fieldErrors.convictions && (
                <div style={{ color: T.danger, fontSize: 12, marginTop: 4 }}>{fieldErrors.convictions}</div>
              )}
            </div>
          </div>

          {/* Population */}
          <div>
            <label style={labelStyle}>Population *</label>
            <input
              type="number"
              style={{ ...inputStyle, borderColor: fieldErrors.population ? T.danger : T.inputBorder }}
              value={form.population}
              onChange={set("population")}
              min={1}
            />
            {fieldErrors.population && (
              <div style={{ color: T.danger, fontSize: 12, marginTop: 4 }}>{fieldErrors.population}</div>
            )}
          </div>

          {/* Submit */}
          <div style={{ marginTop: 24, display: "flex", justifyContent: "flex-end" }}>
            <Button
              onClick={handlePredict}
              disabled={loading}
              style={{
                minWidth: 180,
                padding: "12px 28px",
                fontSize: 15,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
              }}
            >
              {loading ? (
                <>
                  <span style={{
                    display: "inline-block",
                    width: 16,
                    height: 16,
                    border: "2px solid rgba(255,255,255,0.3)",
                    borderTopColor: "#fff",
                    borderRadius: "50%",
                    animation: "spin 0.6s linear infinite",
                  }} />
                  Predicting...
                </>
              ) : (
                "Predict Cases"
              )}
            </Button>
          </div>
        </div>

        {/* Spinner animation */}
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    </PageShell>
  );
}
