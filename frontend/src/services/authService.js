import api from "./api";

export const ROLE_NAMES = { 1: "Supervisor", 2: "Crime Analyst", 3: "Investigator", 4: "Policymaker" };
export const ROLE_IDS = { Supervisor: 1, "Crime Analyst": 2, Investigator: 3, Policymaker: 4 };

function storeAuth(user, tokens) {
  if (!user) {
    console.error("storeAuth: user is undefined, cannot store auth");
    return;
  }
  if (tokens) {
    localStorage.setItem("crimeai_tokens", JSON.stringify(tokens));
  }
  localStorage.setItem("crimeai_user", JSON.stringify({
    id: user.user_id ?? user.id,
    name: user.full_name ?? user.name,
    email: user.email,
    role_id: user.role_id,
    role: ROLE_NAMES[user.role_id] || "Officer",
    phone: user.phone,
  }));
}

/**
 * Extract user and tokens from login API response.
 * Login endpoint returns { user: {...}, tokens: {...} }.
 */
function extractAuthData(responseData) {
  return {
    user: responseData?.user ?? null,
    tokens: responseData?.tokens ?? null,
  };
}

export async function loginAPI(email, password) {
  const r = await api.post("/auth/login", { email, password });
  const { user, tokens } = extractAuthData(r.data);
  storeAuth(user, tokens);
  return r.data;
}

export async function registerAPI(form) {
  const r = await api.post("/auth/register", {
    full_name: form.name,
    email: form.email,
    password: form.password,
    phone: form.phone || null,
    role_id: ROLE_IDS[form.role] || 2,
  });
  // Register endpoint returns UserResponse directly (no tokens).
  // Don't auto-login — redirect to login page to sign in manually.
  return r.data;
}

export function getStoredUser() {
  try { const d = localStorage.getItem("crimeai_user"); return d ? JSON.parse(d) : null; }
  catch { return null; }
}

export function getStoredTokens() {
  try { const d = localStorage.getItem("crimeai_tokens"); return d ? JSON.parse(d) : null; }
  catch { return null; }
}

export function clearAuth() {
  localStorage.removeItem("crimeai_tokens");
  localStorage.removeItem("crimeai_user");
}
