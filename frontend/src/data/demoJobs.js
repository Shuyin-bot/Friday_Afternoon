export const demoJobs = [
  {
    id: "Q-1048",
    title: "Packaging quote — Acme Foods",
    sender: "procurement@acmefoods.com",
    status: "Needs classification",
    time: "2 min ago",
  },
  {
    id: "Q-1047",
    title: "20,000 custom cartons",
    sender: "james@northstar.co",
    status: "Human review",
    time: "18 min ago",
  },
  {
    id: "Q-1046",
    title: "Re: annual supply agreement",
    sender: "orders@greenline.io",
    status: "In progress",
    time: "41 min ago",
  },
  {
    id: "Q-1045",
    title: "Quote request / labels",
    sender: "maya@orbitretail.com",
    status: "Completed",
    time: "1 hr ago",
  },
];

export function mapStats(data) {
  const counts = data.counts || {};
  return {
    classification: counts.PENDING || 0,
    review: (counts.WAITING_FOR_INPUT || 0) + (counts.DRAFTED || 0),
    completed: counts.COMPLETED || 0,
    progress: (counts.CLASSIFIED || 0) + (counts.PROCESSING || 0),
    notQuotation: counts.NOT_QUOTATION || 0,
  };
}

export function mapJobs(jobs) {
  return jobs.map((job) => ({
    rawId: job.id,
    id: `Q-${String(job.id).padStart(4, "0")}`,
    title: job.subject || "Untitled email",
    sender: job.from_email,
    status: job.status.replaceAll("_", " "),
    time: new Date(job.created_at).toLocaleDateString(),
  }));
}
