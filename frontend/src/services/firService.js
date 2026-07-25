import api from "./api";

export async function listFIRs(params = {}) {
  const r = await api.get("/firs", { params });
  return r.data;
}

export async function getFIR(firId) {
  const r = await api.get(`/firs/${firId}`);
  return r.data;
}

export async function createFIR(data) {
  const r = await api.post("/firs", data);
  return r.data;
}

export async function updateFIR(firId, data) {
  const r = await api.patch(`/firs/${firId}`, data);
  return r.data;
}

export async function deleteFIR(firId) {
  await api.delete(`/firs/${firId}`);
}

export async function getFIRStatistics() {
  const r = await api.get("/firs/statistics");
  return r.data;
}

export async function getFIRSummary(firId) {
  const r = await api.get(`/firs/${firId}/summary`);
  return r.data;
}

export async function getFIRTimeline(firId) {
  const r = await api.get(`/firs/${firId}/timeline`);
  return r.data;
}

export async function updateFIRStatus(firId, status) {
  const r = await api.post(`/firs/${firId}/status?status=${encodeURIComponent(status)}`);
  return r.data;
}

export async function getCrimeTypes() {
  const r = await api.get("/firs/crime-types");
  return r.data;
}

export async function getLocations() {
  const r = await api.get("/firs/locations");
  return r.data;
}

export async function getOfficers() {
  const r = await api.get("/firs/officers");
  return r.data;
}
