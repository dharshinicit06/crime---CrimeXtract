import api from "./api";

export async function listHotspots(params = {}) {
  const r = await api.get("/hotspots", { params });
  return r.data;
}

export async function getHotspotDetail(district) {
  const r = await api.get(`/hotspots/${encodeURIComponent(district)}`);
  return r.data;
}

export async function getHotspotMap() {
  const r = await api.get("/hotspots/map");
  return r.data;
}

export async function getHotspotInsights() {
  const r = await api.get("/hotspots/insights");
  return r.data;
}
