import api from "./api";

export async function listTransactions(params = {}) {
  const r = await api.get("/financial-transactions", { params }); return r.data;
}
export async function getTransaction(id) {
  const r = await api.get(`/financial-transactions/${id}`); return r.data;
}
export async function createTransaction(firId, data) {
  const r = await api.post("/financial-transactions", data, { params: { fir_id: firId } }); return r.data;
}
export async function updateTransaction(id, data) {
  const r = await api.patch(`/financial-transactions/${id}`, data); return r.data;
}
export async function deleteTransaction(id) {
  await api.delete(`/financial-transactions/${id}`);
}
export async function getFinancialSummary() {
  const r = await api.get("/financial-transactions/analytics/summary"); return r.data;
}
