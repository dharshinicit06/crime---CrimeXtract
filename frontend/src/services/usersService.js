import api from "./api";

export async function listUsers(params = {}) {
  const r = await api.get("/users", { params }); return r.data;
}
export async function getUser(id) {
  const r = await api.get(`/users/${id}`); return r.data;
}
export async function createUser(data) {
  const r = await api.post("/users", data); return r.data;
}
export async function updateUser(id, data) {
  const r = await api.patch(`/users/${id}`, data); return r.data;
}
export async function deleteUser(id) {
  await api.delete(`/users/${id}`);
}
