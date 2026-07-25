import api from "./api";

export async function getOffenderProfile(accusedId) {
  const r = await api.get(`/offender/${accusedId}`);
  return r.data;
}
