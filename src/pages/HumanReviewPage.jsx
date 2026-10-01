import { useCallback, useEffect, useMemo, useState } from "react";
import { Box, CircularProgress, Stack, Typography } from "@mui/material";
import { CheckCircleRounded } from "@mui/icons-material";
import { jobService } from "../services/jobService";
import { mapJobs } from "../data/demoJobs";
import { HumanReviewCard } from "../components/HumanReviewCard";

export function HumanReviewPage({ onOpenJob, onNotice }) {
  const [requests, setRequests] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState({});
  const [savingId, setSavingId] = useState(null);

  const loadRequests = useCallback(async () => {
    try {
      const [requestsData, jobsData] = await Promise.all([
        jobService.getHumanRequests(),
        jobService.getJobs(),
      ]);
      setRequests(requestsData);
      setJobs(mapJobs(jobsData));
    } catch {
      onNotice(
        "Could not load human review requests — start the API to see live data.",
      );
    } finally {
      setLoading(false);
    }
  }, [onNotice]);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  useEffect(() => jobService.subscribe(loadRequests), [loadRequests]);

  const jobById = useMemo(() => {
    const map = new Map();
    jobs.forEach((job) => map.set(job.rawId, job));
    return map;
  }, [jobs]);

  async function submitAnswer(requestId) {
    const answer = answers[requestId];
    if (!answer || !answer.trim()) return;
    setSavingId(requestId);
    try {
      await jobService.answerHumanRequest(requestId, answer.trim());
      setRequests((current) => current.filter((item) => item.id !== requestId));
      setAnswers((current) => {
        const next = { ...current };
        delete next[requestId];
        return next;
      });
      onNotice("Human answer saved successfully.");
    } catch {
      onNotice("Could not save the human answer.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <>
      <Box mb={4}>
        <Typography
          variant="overline"
          color="primary"
          fontWeight={800}
          letterSpacing=".12em"
        >
          Human-in-the-loop
        </Typography>
        <Typography variant="h3" sx={{ fontSize: { xs: 32, md: 42 }, mt: 0.5 }}>
          Human review
        </Typography>
        <Typography color="text.secondary" mt={1}>
          Decisions the agents are waiting on you for, across every job.
        </Typography>
      </Box>

      {loading ? (
        <Box sx={{ display: "grid", placeItems: "center", minHeight: 300 }}>
          <CircularProgress />
        </Box>
      ) : requests.length ? (
        <Stack spacing={2.5}>
          {requests.map((request) => {
            const job = jobById.get(request.queued_job_id);
            return (
              <Box key={request.id}>
                {job && (
                  <Stack
                    direction="row"
                    justifyContent="space-between"
                    alignItems="center"
                    mb={1}
                    px={0.5}
                  >
                    <Typography variant="body2" color="text.secondary">
                      <strong>{job.title}</strong> &nbsp;•&nbsp; {job.sender}{" "}
                      &nbsp;•&nbsp; {job.time}
                    </Typography>
                    <Typography
                      variant="body2"
                      color="primary"
                      fontWeight={700}
                      sx={{ cursor: "pointer" }}
                      onClick={() => onOpenJob(job)}
                    >
                      Open job →
                    </Typography>
                  </Stack>
                )}
                <HumanReviewCard
                  request={request}
                  answer={answers[request.id] || ""}
                  onAnswerChange={(value) =>
                    setAnswers((current) => ({ ...current, [request.id]: value }))
                  }
                  onSubmit={() => submitAnswer(request.id)}
                  saving={savingId === request.id}
                />
              </Box>
            );
          })}
        </Stack>
      ) : (
        <Box sx={{ py: 10, textAlign: "center" }}>
          <CheckCircleRounded sx={{ color: "#1d9a73", fontSize: 48 }} />
          <Typography fontWeight={800} mt={1.5} fontSize={18}>
            Nothing needs your attention
          </Typography>
          <Typography variant="body2" color="text.secondary" mt={0.5}>
            All human review requests have been answered.
          </Typography>
        </Box>
      )}
    </>
  );
}
