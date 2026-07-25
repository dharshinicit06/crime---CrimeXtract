import api from "./api";

export async function listEvidence(params = {}) {
  const r = await api.get("/evidence", { params }); return r.data;
}
export async function getEvidence(id) {
  const r = await api.get(`/evidence/${id}`); return r.data;
}
export async function createEvidence(firId, data) {
  const r = await api.post("/evidence", data, { params: { fir_id: firId } }); return r.data;
}
export async function updateEvidence(id, data) {
  const r = await api.patch(`/evidence/${id}`, data); return r.data;
}
export async function deleteEvidence(id) {
  await api.delete(`/evidence/${id}`);
}
