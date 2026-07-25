import { useState, useEffect, useMemo } from "react";
import { T } from "../styles/theme";
import { listTransactions, getTransaction, createTransaction, updateTransaction, deleteTransaction, getFinancialSummary } from "../services/financialService";
import { listFIRs } from "../services/firService";
import PageShell from "../components/PageShell";
import Badge from "../components/Badge";
import Button from "../components/Button";
import Input from "../components/Input";
import {
  validateRequired, ACCOUNT_RULES, validateAccount,
  AMOUNT_RULES, validateAmount,
  validateDate, validateRemarks,
  validateForm,
} from "../utils/validation";
import { TrendingUp, DollarSign, AlertTriangle, Banknote, RefreshCw, X, ChevronDown, ChevronUp } from "lucide-react";

const SUSPICIOUS_THRESHOLD = 10_00_000; // ₹10L

function SummaryCard({ icon: Icon, label, value, sub, color, trend }) {
  return (
    <div style={{
      background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 20,
      transition: "all 0.2s",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
        <div style={{ width: 40, height: 40, borderRadius: 12, background: `${color}15`, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Icon size={20} color={color} />
        </div>
        <span style={{ color: T.textMuted, fontSize: 13 }}>{label}</span>
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: T.textPrimary, marginBottom: 2 }}>{value}</div>
      {sub && <div style={{ color: T.textMuted, fontSize: 12 }}>{sub}</div>}
      {trend && (
        <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 4 }}>
          <span style={{ color: trend.color, fontSize: 12 }}>{trend.icon}</span>
          <span style={{ color: trend.color, fontSize: 12 }}>{trend.text}</span>
        </div>
      )}
    </div>
  );
}

function SkeletonCards() {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 24 }}>
      {[1, 2, 3, 4].map(i => (
        <div key={i} style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 20, animation: "pulse 2s infinite" }}>
          <div style={{ height: 12, width: "50%", background: T.inputBorder, borderRadius: 4, marginBottom: 12 }} />
          <div style={{ height: 28, width: "40%", background: T.inputBorder, borderRadius: 6 }} />
        </div>
      ))}
    </div>
  );
}

export default function FinancialTransactions({ user }) {
  const [txns, setTxns] = useState([]);
  const [summary, setSummary] = useState(null);
  const [firOptions, setFirOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ bank_name: "", account_number: "", transaction_reference: "", amount: "", transaction_date: "", transaction_type: "Debit", remarks: "", fir_id: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [saveLoading, setSaveLoading] = useState(false);
  const [formError, setFormError] = useState("");
  const [showSummary, setShowSummary] = useState(true);
  const [summaryExpanded, setSummaryExpanded] = useState(false);

  const canDelete = user?.role_id <= 2;
  const canEdit = user?.role_id <= 3;

  const fetchAll = async () => {
    setLoading(true); setError("");
    try {
      const [t, f, s] = await Promise.all([
        listTransactions({ page_size: 100 }).catch(() => ({ items: [] })),
        listFIRs({ page_size: 200 }).catch(() => ({ items: [] })),
        getFinancialSummary().catch(() => null),
      ]);
      setTxns(t.items || []);
      setFirOptions(f.items || []);
      setSummary(s);
    } catch { setError("Failed to load data"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, []);

  const openCreate = () => {
    setEditId(null);
    setForm({ bank_name: "", account_number: "", transaction_reference: "", amount: "", transaction_date: "", transaction_type: "Debit", remarks: "", fir_id: "" });
    setFieldErrors({}); setFormError(""); setShowForm(true);
  };

  const openEdit = async (id) => {
    try {
      const data = await getTransaction(id);
      setEditId(id);
      setForm({ bank_name: data.bank_name || "", account_number: data.account_number || "", transaction_reference: data.transaction_reference || "", amount: data.amount?.toString() || "", transaction_date: data.transaction_date || "", transaction_type: data.transaction_type || "Debit", remarks: data.remarks || "", fir_id: data.fir_id?.toString() || "" });
      setFieldErrors({}); setFormError(""); setShowForm(true);
    } catch { setFormError("Failed to load transaction details"); }
  };

  const handleSave = async () => {
    const rules = {
      bank_name: [(v) => validateRequired(v, "Bank name"), false],
      account_number: [validateAccount, false],
      transaction_reference: [(v) => validateRequired(v, "Transaction reference"), true],
      amount: [validateAmount, false],
      transaction_date: [(v) => validateDate(v, false, true), false],
      remarks: [validateRemarks, false],
    };
    const errs = validateForm(form, rules);
    setFieldErrors(errs);
    if (Object.keys(errs).length > 0) { setFormError("Please correct the highlighted fields before submitting."); return; }
    setSaveLoading(true); setFormError("");
    try {
      const payload = {
        bank_name: form.bank_name || null, account_number: form.account_number || null,
        transaction_reference: form.transaction_reference, amount: form.amount ? parseFloat(form.amount) : null,
        transaction_date: form.transaction_date || null, transaction_type: form.transaction_type,
        remarks: form.remarks || null,
      };
      const firIdVal = form.fir_id ? parseInt(form.fir_id) : null;
      if (editId) await updateTransaction(editId, payload);
      else await createTransaction(firIdVal, payload);
      setShowForm(false); fetchAll();
    } catch (err) { setFormError(err.response?.data?.detail || "Failed to save transaction"); }
    finally { setSaveLoading(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this transaction?")) return;
    try { await deleteTransaction(id); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || "Failed to delete"); }
  };

  // Bank grouping (computed from transactions)
  const bankGroups = useMemo(() => {
    const groups = {};
    txns.forEach(t => {
      const bank = t.bank_name || "Unknown";
      if (!groups[bank]) groups[bank] = { bank, count: 0, total: 0 };
      groups[bank].count++;
      groups[bank].total += t.amount || 0;
    });
    return Object.values(groups).sort((a, b) => b.total - a.total);
  }, [txns]);

  // Suspicious transactions (high-value or flagged)
  const suspiciousTxns = useMemo(() => {
    return txns.filter(t => (t.amount || 0) >= SUSPICIOUS_THRESHOLD);
  }, [txns]);

  // High-value amount threshold for coloring
  const HIGH_VALUE_COLOR = "#EF4444";
  const SUSPICIOUS_TERMS = ["suspicious", "fraud", "irregular", "alert", "unusual"];

  const isSuspiciousByAmount = (amt) => (amt || 0) >= SUSPICIOUS_THRESHOLD;
  const isSuspiciousByRemarks = (remarks) => {
    if (!remarks) return false;
    const lower = remarks.toLowerCase();
    return SUSPICIOUS_TERMS.some(term => lower.includes(term));
  };

  return (
    <PageShell title="Financial Transactions" user={user}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        @keyframes slideUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
      `}</style>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ color: T.textPrimary, fontSize: 22, fontWeight: 700, margin: 0 }}>Financial Transactions</h1>
          <p style={{ color: T.textMuted, fontSize: 13, marginTop: 4 }}>Transaction monitoring with suspicious activity detection</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={fetchAll} style={{
            padding: "8px 16px", borderRadius: 10, border: `1px solid ${T.cardBorder}`,
            background: T.card, color: T.textSecondary, cursor: "pointer", fontSize: 13,
            display: "flex", alignItems: "center", gap: 6,
          }}>
            <RefreshCw size={14} /> Refresh
          </button>
          <Button onClick={openCreate}>+ New Transaction</Button>
        </div>
      </div>

      {/* Summary Cards */}
      {loading && <SkeletonCards />}

      {summary && !loading && (
        <div style={{ animation: "slideUp 0.3s ease", marginBottom: 24 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 16 }}>
            <SummaryCard icon={Banknote} label="Total Transactions" value={summary.total_count || 0} sub={`Across ${summary.bank_breakdown?.length || 0} banks`} color="#4F8CFF" />
            <SummaryCard icon={DollarSign} label="Total Amount" value={`₹${(summary.total_amount || 0).toLocaleString()}`} sub={`Avg: ₹${(summary.average_amount || 0).toLocaleString()}`} color="#22C55E" />
            <SummaryCard icon={AlertTriangle} label="High-Value" value={summary.high_value_count || 0} sub={`≥ ₹10L flagged`} color="#F59E0B" />
            <SummaryCard icon={TrendingUp} label="Suspicious Alerts" value={summary.suspicious_count || 0} sub="Requires review" color={summary.suspicious_count > 0 ? "#EF4444" : "#22C55E"} />
          </div>

          {/* Bank Breakdown (collapsible) */}
          {summary.bank_breakdown?.length > 0 && (
            <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 12, padding: 16, marginBottom: 16 }}>
              <div
                onClick={() => setSummaryExpanded(!summaryExpanded)}
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
              >
                <h3 style={{ color: T.textPrimary, fontSize: 14, fontWeight: 600, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
                  <Banknote size={16} color={T.textMuted} /> Bank / Account Summary
                </h3>
                {summaryExpanded ? <ChevronUp size={16} color={T.textMuted} /> : <ChevronDown size={16} color={T.textMuted} />}
              </div>
              {summaryExpanded && (
                <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
                  {summary.bank_breakdown.map((b, i) => (
                    <div key={i} style={{
                      display: "flex", justifyContent: "space-between", alignItems: "center",
                      padding: "8px 12px", background: T.inputBg, borderRadius: 8,
                    }}>
                      <div>
                        <span style={{ color: T.textPrimary, fontSize: 13, fontWeight: 500 }}>{b.bank || "Unknown"}</span>
                        <span style={{ color: T.textMuted, fontSize: 11, marginLeft: 8 }}>{b.count} transactions</span>
                      </div>
                      <span style={{ color: T.accent, fontSize: 13, fontWeight: 600 }}>₹{b.total.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Create/Edit Form */}
      {showForm && (
        <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 24, marginBottom: 24, animation: "slideUp 0.3s ease" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ color: T.textPrimary, fontWeight: 600, margin: 0, fontSize: 15 }}>{editId ? "Edit Transaction" : "New Transaction"}</h3>
            <button onClick={() => setShowForm(false)} style={{ padding: 4, borderRadius: 6, border: "none", background: "transparent", color: T.textMuted, cursor: "pointer" }}><X size={16} /></button>
          </div>
          {formError && <div style={{ color: T.danger, fontSize: 13, marginBottom: 12 }}>⚠ {formError}</div>}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Input label="Bank Name" error={fieldErrors.bank_name} value={form.bank_name} onChange={(e) => { setForm({ ...form, bank_name: e.target.value }); setFieldErrors((p) => ({ ...p, bank_name: "" })); }} />
            <Input label="Account Number" error={fieldErrors.account_number} helper={ACCOUNT_RULES.helper} placeholder={ACCOUNT_RULES.placeholder} value={form.account_number} onChange={(e) => { setForm({ ...form, account_number: e.target.value }); setFieldErrors((p) => ({ ...p, account_number: "" })); }} />
            <Input label="Transaction Reference" required error={fieldErrors.transaction_reference} value={form.transaction_reference} onChange={(e) => { setForm({ ...form, transaction_reference: e.target.value }); setFieldErrors((p) => ({ ...p, transaction_reference: "" })); }} />
            <Input label="Amount" type="number" step="0.01" error={fieldErrors.amount} placeholder={AMOUNT_RULES.placeholder} value={form.amount} onChange={(e) => { setForm({ ...form, amount: e.target.value }); setFieldErrors((p) => ({ ...p, amount: "" })); }} />
            <Input label="Transaction Date" type="date" error={fieldErrors.transaction_date} value={form.transaction_date} onChange={(e) => { setForm({ ...form, transaction_date: e.target.value }); setFieldErrors((p) => ({ ...p, transaction_date: "" })); }} />
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, color: T.textSecondary, marginBottom: 6, fontWeight: 500 }}>Type</label>
              <select value={form.transaction_type} onChange={(e) => setForm({ ...form, transaction_type: e.target.value })}
                style={{ width: "100%", padding: "12px 14px", background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 10, color: T.textPrimary, fontSize: 14, outline: "none" }}>
                {["Debit","Credit","Transfer","Cash","Other"].map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, color: T.textSecondary, marginBottom: 6, fontWeight: 500 }}>Linked FIR</label>
              <select value={form.fir_id} onChange={(e) => { setForm({ ...form, fir_id: e.target.value }); setFieldErrors((p) => ({ ...p, fir_id: "" })); }}
                style={{ width: "100%", padding: "12px 14px", background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 10, color: T.textPrimary, fontSize: 14, outline: "none" }}>
                <option value="">— None —</option>
                {firOptions.map((f) => <option key={f.fir_id} value={f.fir_id}>{f.fir_number}</option>)}
              </select>
            </div>
          </div>
          <Input label="Remarks" error={fieldErrors.remarks} value={form.remarks} onChange={(e) => { setForm({ ...form, remarks: e.target.value }); setFieldErrors((p) => ({ ...p, remarks: "" })); }} />
          <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
            <Button onClick={handleSave} disabled={saveLoading}>{saveLoading ? "Saving..." : "Save"}</Button>
            <Button variant="secondary" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {/* Transactions Table */}
      <div style={{ background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>Loading transactions...</div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: "center", color: T.danger, fontSize: 14 }}>⚠ {error}</div>
        ) : txns.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: T.textMuted, fontSize: 14 }}>No transactions found</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                  {["Reference", "Bank", "Account", "Amount", "Date", "Type", "Status", "FIR", "Actions"].map((h) => (
                    <th key={h} style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "left", padding: "14px 16px", textTransform: "uppercase", letterSpacing: "0.5px", whiteSpace: "nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {txns.map((t, i) => {
                  const fir = firOptions.find((f) => f.fir_id === t.fir_id);
                  const txId = t.transaction_id ?? t.id ?? i;
                  const isHighValue = isSuspiciousByAmount(t.amount);
                  const isSuspiciousRemark = isSuspiciousByRemarks(t.remarks);
                  const isSuspicious = isHighValue || isSuspiciousRemark;
                  const amountColor = isHighValue ? T.danger : isSuspiciousRemark ? T.warning : T.accent;
                  return (
                    <tr key={txId} style={{
                      borderBottom: i < txns.length - 1 ? `1px solid ${T.cardBorder}` : "none",
                      background: isSuspicious ? "rgba(239,68,68,0.04)" : "transparent",
                      transition: "background 0.15s",
                    }}>
                      <td style={{ padding: "14px 16px", color: T.textPrimary, fontSize: 13, fontWeight: 600, whiteSpace: "nowrap" }}>
                        {t.transaction_reference}
                      </td>
                      <td style={{ padding: "14px 16px", color: T.textSecondary, fontSize: 12, whiteSpace: "nowrap" }}>
                        {t.bank_name || "—"}
                      </td>
                      <td style={{ padding: "14px 16px", color: T.textMuted, fontSize: 12, fontFamily: "monospace" }}>
                        {t.account_number ? `****${t.account_number.slice(-4)}` : "—"}
                      </td>
                      <td style={{ padding: "14px 16px", color: amountColor, fontSize: 13, fontWeight: 700, whiteSpace: "nowrap" }}>
                        ₹{t.amount != null ? Number(t.amount).toLocaleString() : "—"}
                        {isHighValue && <span style={{ marginLeft: 6, fontSize: 10, color: T.danger }}>⚠</span>}
                      </td>
                      <td style={{ padding: "14px 16px", color: T.textSecondary, fontSize: 12, whiteSpace: "nowrap" }}>
                        {t.transaction_date ? t.transaction_date.slice(0, 10) : "—"}
                      </td>
                      <td style={{ padding: "14px 16px", whiteSpace: "nowrap" }}>
                        <Badge label={t.transaction_type || "—"} />
                      </td>
                      <td style={{ padding: "14px 16px", whiteSpace: "nowrap" }}>
                        {isSuspicious ? (
                          <Badge label="⚠ Flagged" />
                        ) : (
                          <Badge label="Normal" />
                        )}
                      </td>
                      <td style={{ padding: "14px 16px", color: T.textSecondary, fontSize: 12, whiteSpace: "nowrap" }}>
                        {fir?.fir_number || `#${t.fir_id || "—"}`}
                      </td>
                      <td style={{ padding: "14px 16px", whiteSpace: "nowrap" }}>
                        <div style={{ display: "flex", gap: 6 }}>
                          {canEdit && <button onClick={() => openEdit(t.transaction_id ?? t.id)} style={{ background: T.accentGlow, color: T.accent, border: "none", padding: "5px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>Edit</button>}
                          {canDelete && <button onClick={() => handleDelete(t.transaction_id ?? t.id)} style={{ background: "rgba(239,68,68,0.15)", color: T.danger, border: "none", padding: "5px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer" }}>Delete</button>}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Suspicious Transactions Section */}
      {!loading && suspiciousTxns.length > 0 && (
        <div style={{
          marginTop: 24, background: T.card, border: `1px solid rgba(239,68,68,0.2)`, borderRadius: 16, padding: 20,
          animation: "slideUp 0.4s ease",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
            <div style={{ width: 32, height: 32, borderRadius: 10, background: "rgba(239,68,68,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <AlertTriangle size={16} color="#EF4444" />
            </div>
            <h3 style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600, margin: 0 }}>⚠ High-Value & Suspicious Transactions</h3>
            <Badge label={`${suspiciousTxns.length} flagged`} />
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${T.cardBorder}` }}>
                  <th style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "left", padding: "10px 12px", textTransform: "uppercase", letterSpacing: 0.5 }}>Reference</th>
                  <th style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "left", padding: "10px 12px", textTransform: "uppercase", letterSpacing: 0.5 }}>Bank</th>
                  <th style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "right", padding: "10px 12px", textTransform: "uppercase", letterSpacing: 0.5 }}>Amount</th>
                  <th style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "center", padding: "10px 12px", textTransform: "uppercase", letterSpacing: 0.5 }}>Date</th>
                  <th style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "center", padding: "10px 12px", textTransform: "uppercase", letterSpacing: 0.5 }}>Type</th>
                  <th style={{ color: T.textMuted, fontSize: 11, fontWeight: 600, textAlign: "center", padding: "10px 12px", textTransform: "uppercase", letterSpacing: 0.5 }}>Risk</th>
                </tr>
              </thead>
              <tbody>
                {suspiciousTxns.map((t, i) => (
                  <tr key={t.transaction_id || i} style={{ borderBottom: i < suspiciousTxns.length - 1 ? `1px solid ${T.cardBorder}` : "none" }}>
                    <td style={{ padding: "10px 12px", color: T.textPrimary, fontSize: 13, fontWeight: 600 }}>{t.transaction_reference}</td>
                    <td style={{ padding: "10px 12px", color: T.textSecondary, fontSize: 12 }}>{t.bank_name || "—"}</td>
                    <td style={{ padding: "10px 12px", color: T.danger, fontSize: 13, fontWeight: 700, textAlign: "right" }}>₹{Number(t.amount).toLocaleString()}</td>
                    <td style={{ padding: "10px 12px", color: T.textSecondary, fontSize: 12, textAlign: "center" }}>{t.transaction_date ? t.transaction_date.slice(0, 10) : "—"}</td>
                    <td style={{ padding: "10px 12px", textAlign: "center" }}><Badge label={t.transaction_type || "—"} /></td>
                    <td style={{ padding: "10px 12px", textAlign: "center" }}>
                      <Badge label={isSuspiciousByAmount(t.amount) ? "High Value" : "Flagged"} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Bank Group Summary (bottom) */}
      {!loading && bankGroups.length > 0 && (
        <div style={{
          marginTop: 16, background: T.card, border: `1px solid ${T.cardBorder}`, borderRadius: 16, padding: 20,
        }}>
          <h3 style={{ color: T.textPrimary, fontSize: 15, fontWeight: 600, margin: "0 0 12px", display: "flex", alignItems: "center", gap: 8 }}>
            <Banknote size={16} color={T.textMuted} /> Transactions by Bank
          </h3>
          <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))" }}>
            {bankGroups.map((g, i) => (
              <div key={i} style={{
                padding: "12px 14px", background: T.inputBg, borderRadius: 10,
                border: `1px solid ${T.cardBorder}`,
              }}>
                <div style={{ color: T.textPrimary, fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{g.bank}</div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: T.textMuted, fontSize: 12 }}>{g.count} transactions</span>
                  <span style={{ color: T.accent, fontSize: 13, fontWeight: 600 }}>₹{g.total.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </PageShell>
  );
}
