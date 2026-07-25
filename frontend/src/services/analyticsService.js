import api from "./api";

export async function getSummary() {
  const r = await api.get("/analytics/summary");
  return r.data;
}

export async function getCrimeByMonth(year) {
  const r = await api.get("/analytics/crime-by-month", { params: { year } });
  return r.data;
}

export async function getCrimeByDistrict() {
  const r = await api.get("/analytics/crime-by-district");
  return r.data;
}

export async function getCrimeByType() {
  const r = await api.get("/analytics/crime-by-type");
  return r.data;
}

export async function getSolvedVsPending() {
  const r = await api.get("/analytics/solved-vs-pending");
  return r.data;
}

export async function getGenderWise() {
  const r = await api.get("/analytics/gender-wise");
  return r.data;
}

export async function getAgeWise() {
  const r = await api.get("/analytics/age-wise");
  return r.data;
}

export async function getTopHotspots(limit = 10) {
  const r = await api.get("/analytics/top-hotspots", { params: { limit } });
  return r.data;
}

export async function getDashboard() {
  const r = await api.get("/analytics/dashboard");
  return r.data;
}

export async function getPredictions() {
  const r = await api.get("/analytics/predictions");
  return r.data;
}

export async function getPerformance() {
  const r = await api.get("/analytics/performance");
  return r.data;
}

export async function getRealtime() {
  const r = await api.get("/analytics/realtime");
  return r.data;
}
