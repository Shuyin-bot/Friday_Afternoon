import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Box,
  Button,
  CircularProgress,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import {
  EmailRounded,
  SearchRounded,
} from "@mui/icons-material";
import { jobService } from "../services/jobService";
import { mapJobs } from "../data/demoJobs";
import { ActivityList } from "../components/ActivityList";
import { StatusCards } from "../components/StatusCards";
import { filterJobsByCard, filterJobsBySearch } from "../utils/jobFilters";

const queueCardLabels = {
  progress: "In progress",
  review: "Human review",
  completed: "Completed",
};

const quotationStatuses = new Set([
  "CLASSIFIED",
  "EXTRACTED",
  "RESEARCH_EXT",
  "RESEARCH_INT",
  "DRAFTED",
  "WAITING_FOR_INPUT",
  "FAILED",
  "COMPLETED",
]);

export function EmailQueuePage({ onOpenJob, onNotice, pageTitle = "Email queue" }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeChip, setActiveChip] = useState(null);
  const [search, setSearch] = useState("");
  const [busyAction, setBusyAction] = useState("");

  const loadJobs = useCallback(async () => {
    try {
      const jobsData = await jobService.getJobs();
      setJobs(mapJobs(jobsData.filter((job) => quotationStatuses.has(job.status))));
    } catch {
      onNotice("Could not load the email queue — start the API to see live jobs.");
    } finally {
      setLoading(false);
    }
  }, [onNotice]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  useEffect(() => jobService.subscribe(loadJobs), [loadJobs]);

  async function fetchEmails() {
    setBusyAction("Fetch emails");
    try {
      await jobService.trigger("retrieve");
      onNotice(
        "Email fetch started. Gmail messages are being retrieved, and missing mock leads will be added automatically.",
      );
    } catch {
      onNotice("Could not reach the API. Fetch emails is ready once the backend is running.");
    } finally {
      setBusyAction("");
    }
  }

  const visibleJobs = useMemo(() => {
    const byCard = filterJobsByCard(jobs, activeChip);
    return filterJobsBySearch(byCard, search);
  }, [jobs, activeChip, search]);

  const queueStats = useMemo(
    () => ({
      progress: filterJobsByCard(jobs, "progress").length,
      review: filterJobsByCard(jobs, "review").length,
      completed: filterJobsByCard(jobs, "completed").length,
    }),
    [jobs],
  );

  return (
    <>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        mb={4}
      >
        <Box>
          <Typography
            variant="overline"
            color="primary"
            fontWeight={800}
            letterSpacing=".12em"
          >
            Pipeline
          </Typography>
          <Typography variant="h3" sx={{ fontSize: { xs: 32, md: 42 }, mt: 0.5 }}>
            {pageTitle}
          </Typography>
          <Typography color="text.secondary" mt={1}>
            Quotation emails recognized by the pipeline.
          </Typography>
        </Box>
        <Button
          size="small"
          variant="outlined"
          startIcon={
            busyAction === "Fetch emails" ? (
              <CircularProgress size={14} />
            ) : (
              <EmailRounded fontSize="small" />
            )
          }
          onClick={fetchEmails}
          disabled={!!busyAction}
          sx={{ alignSelf: { xs: "flex-start", sm: "center" }, height: "fit-content" }}
        >
          Fetch emails
        </Button>
      </Stack>

      <StatusCards
        stats={queueStats}
        activeCard={activeChip}
        onSelect={(key) => setActiveChip(activeChip === key ? null : key)}
        cardKeys={["progress", "review", "completed"]}
      />

      <Stack direction="row" justifyContent="flex-end" mb={3}>
        <TextField
          size="small"
          placeholder="Search by subject or sender..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          sx={{ minWidth: { xs: "100%", md: 280 }, bgcolor: "white" }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchRounded fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
      </Stack>

      {loading ? (
        <Box sx={{ display: "grid", placeItems: "center", minHeight: 300 }}>
          <CircularProgress />
        </Box>
      ) : (
        <ActivityList
          jobs={visibleJobs}
          title={
            activeChip
              ? queueCardLabels[activeChip]
              : "Recognized quotation emails"
          }
          subtitle="Click a job to open its review workspace."
          onRefresh={loadJobs}
          onOpen={onOpenJob}
          showIndex
        />
      )}
    </>
  );
}
