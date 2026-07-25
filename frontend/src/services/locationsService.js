import api from "./api";

export async function listLocations(params = {}) {
  const r = await api.get("/locations", { params }); return r.data;
}
export async function getLocation(id) {
  const r = await api.get(`/locations/${id}`); return r.data;
}
export async function createLocation(data) {
  const r = await api.post("/locations", data); return r.data;
}
export async function updateLocation(id, data) {
  const r = await api.patch(`/locations/${id}`, data); return r.data;
}
export async function deleteLocation(id) {
  await api.delete(`/locations/${id}`);
}
export async function getLocationUsage(id) {
  const r = await api.get(`/locations/${id}/usage`); return r.data;
}
export async function getLocationStatistics() {
  const r = await api.get("/locations/statistics"); return r.data;
}
