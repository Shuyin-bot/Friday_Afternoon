const statusVisuals = {
  PENDING: { color: "#e86b48", soft: "#fff0eb" },
  CLASSIFIED: { color: "#d5961b", soft: "#fff7df" },
  EXTRACTED: { color: "#d5961b", soft: "#fff7df" },
  RESEARCH_EXT: { color: "#d5961b", soft: "#fff7df" },
  RESEARCH_INT: { color: "#d5961b", soft: "#fff7df" },
  DRAFTED: { color: "#8e5bd9", soft: "#f3edff" },
  WAITING_FOR_INPUT: { color: "#8e5bd9", soft: "#f3edff" },
  FAILED: { color: "#e86b48", soft: "#fff0eb" },
  NOT_QUOTATION: { color: "#718096", soft: "#eef1f5" },
  COMPLETED: { color: "#1d9a73", soft: "#e8faf3" },
};

export function getStatusVisual(status) {
  const key = String(status || "").toUpperCase().replaceAll(" ", "_");
  return statusVisuals[key] || { color: "#718096", soft: "#eef1f5" };
}
