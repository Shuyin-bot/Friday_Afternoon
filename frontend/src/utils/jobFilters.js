// Shared status-bucket filter used by the Dashboard status cards and the
// Email queue page's filter chips, so "classification" / "review" / etc.
// mean the same thing everywhere in the app.
export function filterJobsByCard(jobs, activeCard) {
  if (!activeCard) return jobs;
  return jobs.filter((job) => {
    const status = job.status.toLowerCase();
    if (activeCard === "classification")
      return status.includes("pending") || status.includes("classification");
    if (activeCard === "review")
      return (
        status.includes("waiting") ||
        status.includes("review") ||
        status.includes("draft")
      );
    if (activeCard === "progress")
      return (
        status.includes("classif") ||
        status.includes("extract") ||
        status.includes("research") ||
        status.includes("progress") ||
        status.includes("processing")
      );
    if (activeCard === "completed") return status.includes("complete");
    return status.includes("not quotation") || status.includes("not_quotation");
  });
}

export function filterJobsBySearch(jobs, query) {
  const trimmed = query.trim().toLowerCase();
  if (!trimmed) return jobs;
  return jobs.filter((job) =>
    `${job.title} ${job.sender}`.toLowerCase().includes(trimmed),
  );
}
