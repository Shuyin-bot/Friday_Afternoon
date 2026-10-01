import { API_URL } from "../config/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

export const jobService = {
  getStats: () => request("/api/stats"),
  getJobs: () => request("/api/jobs"),
  getJob: (id) => request(`/api/jobs/${id}`),
  getHumanRequests: () => request("/api/human-requests"),
  getHumanRequestHistory: () => request("/api/human-requests/history"),
  answerHumanRequest: (id, answer) =>
    request(`/api/human-requests/${id}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    }),
  approveDraft: (id) => request(`/api/jobs/${id}/approve`, { method: "POST" }),
  unapproveDraft: (id) => request(`/api/jobs/${id}/unapprove`, { method: "POST" }),
  updateDraft: (id, draft) =>
    request(`/api/jobs/${id}/draft`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(draft),
    }),
  rejectDraft: (id) => request(`/api/jobs/${id}/reject`, { method: "POST" }),
  sendDraftBackForRevision: (id, comment) =>
    request(`/api/jobs/${id}/review-comment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ comment }),
    }),
  trigger: (action) => request(`/api/run/${action}`, { method: "POST" }),
  subscribe: (onStatusChange) => {
    const source = new EventSource(`${API_URL}/api/events`);
    source.addEventListener("job_status", onStatusChange);
    return () => source.close();
  },
};
