import api from "./api";

export async function getNetwork(firId) {
  const r = await api.get("/network", { params: { fir_id: firId || undefined } });
  return r.data;
}

export async function getNetworkGraph(firNumber) {
  const r = await api.get(`/network/${encodeURIComponent(firNumber)}`);
  return r.data;
}
