import api from "./api";

export async function getProfile() {
  const r = await api.get("/settings/profile");
  return r.data;
}

export async function updateProfile(data) {
  const r = await api.patch("/settings/profile", data);
  return r.data;
}

export async function changePassword(currentPassword, newPassword) {
  const r = await api.post("/settings/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return r.data;
}

export async function getPreferences() {
  const r = await api.get("/settings/preferences");
  return r.data;
}

export async function updatePreferences(data) {
  const r = await api.patch("/settings/preferences", data);
  return r.data;
}

export async function getSystemInfo() {
  const r = await api.get("/settings/system");
  return r.data;
}

export async function logoutAllSessions() {
  const r = await api.post("/settings/logout-all");
  return r.data;
}
