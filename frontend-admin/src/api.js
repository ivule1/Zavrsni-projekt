const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(errorCode, message) {
    super(message);
    this.errorCode = errorCode;
  }
}

async function adminRequest(path, token, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new ApiError("NETWORK_ERROR", "Nije moguce spojiti se na backend.");
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new ApiError(data.error_code || "UNKNOWN_ERROR", data.message || "Doslo je do greske.");
  }

  return data;
}

export function adminLogin(username, password) {
  return adminRequest("/auth/login", null, {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

// --- Izbori -----------------------------------------------------------------

export function listElections(token) {
  return adminRequest("/elections", token);
}

export function createElection(token, name, scheduledOpenAt = null, scheduledCloseAt = null) {
  return adminRequest("/elections", token, {
    method: "POST",
    body: JSON.stringify({
      name,
      scheduled_open_at: scheduledOpenAt,
      scheduled_close_at: scheduledCloseAt,
    }),
  });
}

export function listCandidates(token, electionId) {
  return adminRequest(`/elections/${electionId}/candidates`, token);
}

export function addCandidate(token, electionId, name) {
  return adminRequest(`/elections/${electionId}/candidates`, token, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function bulkAddCandidates(token, electionId, names) {
  return adminRequest(`/elections/${electionId}/candidates/bulk`, token, {
    method: "POST",
    body: JSON.stringify({ candidates: names.map((name) => ({ name })) }),
  });
}

export function openElection(token, electionId) {
  return adminRequest(`/elections/${electionId}/open`, token, { method: "POST" });
}

export function closeElection(token, electionId) {
  return adminRequest(`/elections/${electionId}/close`, token, { method: "POST" });
}

export function getVoteCounts(token, electionId) {
  return adminRequest(`/elections/${electionId}/vote-counts`, token);
}

export function tallyElection(token, electionId, privateKeyPem) {
  return adminRequest(`/elections/${electionId}/tally`, token, {
    method: "POST",
    body: JSON.stringify({ private_key_pem: privateKeyPem }),
  });
}

export function getDeviceVoteCounts(token, electionId) {
  return adminRequest(`/elections/${electionId}/device-vote-counts`, token);
}

// --- Biracka mjesta -----------------------------------------------------------------

export function listStations(token) {
  return adminRequest("/stations", token);
}

export function createStation(token, station) {
  return adminRequest("/stations", token, {
    method: "POST",
    body: JSON.stringify(station),
  });
}

export function bulkCreateStations(token, stations) {
  return adminRequest("/stations/bulk", token, {
    method: "POST",
    body: JSON.stringify({ stations }),
  });
}

// --- Uredjaji -----------------------------------------------------------------

export function listDevices(token, stationId) {
  return adminRequest(`/stations/${stationId}/devices`, token);
}

export function registerDevice(token, stationId, deviceCode) {
  return adminRequest(`/stations/${stationId}/devices`, token, {
    method: "POST",
    body: JSON.stringify({ device_code: deviceCode }),
  });
}

export function bulkRegisterDevices(token, stationIds, skipExisting = true) {
  return adminRequest("/devices/bulk-register", token, {
    method: "POST",
    body: JSON.stringify({ station_ids: stationIds, skip_existing: skipExisting }),
  });
}

// --- Tokeni -----------------------------------------------------------------

export function getTokenSummary(token, stationId) {
  return adminRequest(`/stations/${stationId}/tokens/summary`, token);
}

export function generateTokens(token, stationId, count, force = false) {
  return adminRequest(`/stations/${stationId}/tokens/generate`, token, {
    method: "POST",
    body: JSON.stringify({ count: count || null, force }),
  });
}

export function bulkGenerateTokens(token, stationIds, count, force = false) {
  return adminRequest("/tokens/bulk-generate", token, {
    method: "POST",
    body: JSON.stringify({ station_ids: stationIds, count: count || null, force }),
  });
}

// --- Audit / sigurnosni dogadaji (FAZA 9 dopuna, poglavlje 16) --------------

export function getAuditLogs(token, { limit = 50, before = null, eventType = null } = {}) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (before) params.set("before", before);
  if (eventType) params.set("event_type", eventType);
  return adminRequest(`/audit-logs?${params.toString()}`, token);
}
