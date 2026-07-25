import api from "./api";

export async function listVictims(params = {}) {
  const r = await api.get("/victims", { params }); return r.data;
}
export async function getVictim(id) {
  const r = await api.get(`/victims/${id}`); return r.data;
}
export async function createVictim(firId, data) {
  const r = await api.post("/victims", data, { params: { fir_id: firId } }); return r.data;
}
export async function updateVictim(id, data) {
  const r = await api.patch(`/victims/${id}`, data); return r.data;
}
export async function deleteVictim(id) {
  await api.delete(`/victims/${id}`);
}
