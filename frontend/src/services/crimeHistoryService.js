import api from "./api";

export async function listCrimeHistory(params = {}) {
  const r = await api.get("/crime-history", { params }); return r.data;
}
export async function getCrimeHistory(id) {
  const r = await api.get(`/crime-history/${id}`); return r.data;
}
export async function createCrimeHistory(data) {
  const r = await api.post("/crime-history", data); return r.data;
}
export async function updateCrimeHistory(id, data) {
  const r = await api.patch(`/crime-history/${id}`, data); return r.data;
}
export async function deleteCrimeHistory(id) {
  await api.delete(`/crime-history/${id}`);
}
export async function getRepeatOffenders(params = {}) {
  const r = await api.get("/crime-history/repeat-offenders", { params }); return r.data;
}
