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
