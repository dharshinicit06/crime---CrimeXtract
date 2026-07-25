import api from "./api";

export async function listAccused(params = {}) {
  const r = await api.get("/accused", { params }); return r.data;
}
export async function getAccused(id) {
  const r = await api.get(`/accused/${id}`); return r.data;
}
export async function createAccused(data) {
  const r = await api.post("/accused", data); return r.data;
}
export async function updateAccused(id, data) {
  const r = await api.patch(`/accused/${id}`, data); return r.data;
}
export async function deleteAccused(id) {
  await api.delete(`/accused/${id}`);
}
