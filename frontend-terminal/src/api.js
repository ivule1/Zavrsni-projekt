const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const DEVICE_KEY = import.meta.env.VITE_DEVICE_KEY || "";
// FAZA 9 (bonus) - /ws/status je bez autentikacije (vidi backend), pa
// terminalu ne treba device kljuc ni za ovu vezu
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(errorCode, message) {
    super(message);
    this.errorCode = errorCode;
  }
}

async function deviceRequest(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Device-Key": DEVICE_KEY,
        ...(options.headers || {}),
      },
    });
  } catch {
    // mreza nedostupna / backend ugasen - poglavlje 25, dostupnost
    throw new ApiError("NETWORK_ERROR", "Nije moguce spojiti se na sustav.");
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(data.error_code || "UNKNOWN_ERROR", data.message || "Doslo je do greske.");
  }

  return data;
}

export function validateToken(token) {
  return deviceRequest("/tokens/validate", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export function getCurrentElection() {
  return deviceRequest("/voting/current-election");
}

export function castVote(token, candidateId) {
  return deviceRequest("/voting/cast", {
    method: "POST",
    body: JSON.stringify({ token, candidate_id: candidateId }),
  });
}
