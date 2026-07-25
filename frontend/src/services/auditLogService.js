import api from "./api";

export async function listAuditLogs(params = {}) {
  const r = await api.get("/audit-logs", { params }); return r.data;
}
export async function getAuditLog(id) {
  const r = await api.get(`/audit-logs/${id}`); return r.data;
}
export async function getAuditStats() {
  const r = await api.get("/audit-logs/stats"); return r.data;
}
export async function purgeAuditLogs(days) {
  const r = await api.delete("/audit-logs/purge", { params: { days } }); return r.data;
}
export async function getMyActivity() {
  const r = await api.get("/audit-logs/my-activity"); return r.data;
}
