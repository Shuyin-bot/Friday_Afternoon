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

  const loadRequests = useCallback(async () => {
    try {
      const [historyData, jobsData] = await Promise.all([
        jobService.getHumanRequestHistory(),
        jobService.getJobs(),
      ]);
      setRequests(historyData);
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
          Previously approved human decisions across the quotation pipeline.
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
                  readOnly
                />
              </Box>
            );
          })}
        </Stack>
      ) : (
        <Box sx={{ py: 10, textAlign: "center" }}>
          <CheckCircleRounded sx={{ color: "#1d9a73", fontSize: 48 }} />
          <Typography fontWeight={800} mt={1.5} fontSize={18}>
            No approved human reviews yet
          </Typography>
          <Typography variant="body2" color="text.secondary" mt={0.5}>
            Approved human decisions will appear here.
          </Typography>
        </Box>
      )}
    </>
  );
}
