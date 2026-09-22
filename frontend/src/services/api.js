const BASE = import.meta.env.VITE_API_URL || "http://localhost:5001";

async function request(path, options = {}) {
  const token = localStorage.getItem("sthira_token");
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

export const api = {
  signup: (body) => request("/api/auth/signup", { method: "POST", body: JSON.stringify(body) }),
  login: (body) => request("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  me: () => request("/api/auth/me"),
  poses: () => request("/api/poses"),
  sessions: () => request("/api/sessions"),
  session: (id) => request(`/api/sessions/${id}`),
  dashboard: () => request("/api/dashboard"),
  baseUrl: BASE,
};
