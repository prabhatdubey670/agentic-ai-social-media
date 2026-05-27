const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function fetchDashboardData() {
  const res = await fetch(`${API_BASE_URL}/api/dashboard`);
  if (!res.ok) throw new Error("Failed to fetch dashboard data");
  return res.json();
}

export async function fetchQueue() {
  const res = await fetch(`${API_BASE_URL}/api/queue`);
  if (!res.ok) throw new Error("Failed to fetch queue");
  return res.json();
}

export async function approvePost(id: string) {
  const res = await fetch(`${API_BASE_URL}/api/queue/${id}/approve`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to approve post");
  return res.json();
}

export async function runAgent(mode: string) {
  const res = await fetch(`${API_BASE_URL}/api/agent/run?mode=${mode}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to run agent");
  return res.json();
}

export async function generateInstant(topic: string, platform: string) {
  const res = await fetch(`${API_BASE_URL}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic, platform }),
  });
  if (!res.ok) throw new Error("Failed to generate content");
  return res.json();
}

export async function publishInstant(text: string, platform: string) {
  const res = await fetch(`${API_BASE_URL}/api/publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, platform }),
  });
  if (!res.ok) throw new Error("Failed to publish content");
  return res.json();
}

export async function fetchProfileStats() {
  const res = await fetch(`${API_BASE_URL}/api/profile`);
  if (!res.ok) throw new Error("Failed to fetch profile stats");
  return res.json();
}

export async function fetchWorldUpdate() {
  const res = await fetch(`${API_BASE_URL}/api/world-update`);
  if (!res.ok) throw new Error("Failed to fetch world update");
  return res.json();
}

export async function fetchSuggestedPeers() {
  const res = await fetch(`${API_BASE_URL}/api/peers/suggest`);
  if (!res.ok) throw new Error("Failed to fetch suggested peers");
  return res.json();
}

export async function addManualPeer(handle: string, platform: string, url: string = "") {
  const res = await fetch(`${API_BASE_URL}/api/peers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ handle, platform, url }),
  });
  if (!res.ok) throw new Error("Failed to add peer");
  return res.json();
}
