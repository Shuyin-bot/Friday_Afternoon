import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Box,
  Button,
  Card,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";
import {
  EmailRounded,
  PlayArrowRounded,
  TuneRounded,
  WarningAmberRounded,
} from "@mui/icons-material";
import { jobService } from "../services/jobService";
import { demoJobs, mapJobs, mapStats } from "../data/demoJobs";
import { StatusCards } from "../components/StatusCards";
import { ActivityList } from "../components/ActivityList";
import { filterJobsByCard } from "../utils/jobFilters";

export function DashboardPage({ onOpenJob, onNotice }) {
  const [stats, setStats] = useState({
    classification: 12,
    review: 4,
    completed: 86,
    progress: 9,
    notQuotation: 18,
  });
  const [jobs, setJobs] = useState(demoJobs);
  const [activeCard, setActiveCard] = useState(null);
  const [busyAction, setBusyAction] = useState("");

  const loadDashboard = useCallback(async () => {
    try {
      const [statsData, jobsData] = await Promise.all([
        jobService.getStats(),
        jobService.getJobs(),
      ]);
      setStats(mapStats(statsData));
      setJobs(mapJobs(jobsData));
    } catch {
      onNotice("Showing preview data — start the API to see live jobs.");
    }
  }, [onNotice]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => jobService.subscribe(loadDashboard), [loadDashboard]);

  async function trigger(action, label) {
    setBusyAction(label);
    try {
      await jobService.trigger(action);
      onNotice(
        action === "retrieve"
          ? "Email fetch started. Gmail messages are being retrieved, and missing mock leads will be added automatically."
          : `${label} started successfully.`,
      );
    } catch {
      onNotice(
        `Could not reach the API. ${label} is ready once the backend is running.`,
      );
    } finally {
      setBusyAction("");
    }
  }

  const visibleJobs = useMemo(
    () => filterJobsByCard(jobs, activeCard),
    [jobs, activeCard],
  );
  const selectedLabel =
    activeCard &&
    {
      classification: "Needs classification",
      review: "Human review",
      progress: "In progress",
      completed: "Completed",
      notQuotation: "Not quotation",
    }[activeCard];

  return (
    <>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={2}
        mb={5}
      >
        <Box>
          <Typography
            variant="overline"
            color="primary"
            fontWeight={800}
            letterSpacing=".12em"
          >
            Saturday, 26 September 2026
          </Typography>
          <Typography
            variant="h3"
            sx={{ fontSize: { xs: 32, md: 42 }, mt: 0.5 }}
          >
            Good afternoon, Pack Flow <span>✦</span>
          </Typography>
          <Typography color="text.secondary" mt={1}>
            Here’s the pulse of your quotation pipeline.
          </Typography>
        </Box>
        <Stack
          direction="row"
          spacing={1}
          alignItems="center"
          sx={{ alignSelf: { xs: "center", sm: "auto" }, width: "fit-content" }}
        >
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
            onClick={() => trigger("retrieve", "Fetch emails")}
            disabled={!!busyAction}
            sx={{ alignSelf: "center", height: "fit-content" }}
          >
            Fetch emails
          </Button>
          <Button
            size="small"
            variant="contained"
            startIcon={
              busyAction === "Run workflow" ? (
                <CircularProgress size={14} color="inherit" />
              ) : (
                <PlayArrowRounded fontSize="small" />
              )
            }
            onClick={() => trigger("workflow", "Run workflow")}
            disabled={!!busyAction}
            sx={{ alignSelf: "center", height: "fit-content" }}
          >
            Run workflow
          </Button>
        </Stack>
      </Stack>
      <StatusCards
        stats={stats}
        activeCard={activeCard}
        onSelect={setActiveCard}
      />
      <ActivityList
        jobs={visibleJobs}
        title={selectedLabel || "Latest activity"}
        subtitle={
          selectedLabel
            ? "Click a job to open its review workspace."
            : "A clear view of what needs attention next."
        }
        onRefresh={loadDashboard}
        onOpen={onOpenJob}
      />
      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
        <Card
          sx={{
            flex: 1,
            p: 2.5,
            bgcolor: "#18254a",
            color: "white",
            border: 0,
          }}
        >
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="center"
          >
            <Box>
              <Typography
                variant="overline"
                sx={{ color: "#aebcf5", fontWeight: 800 }}
              >
                Quick action
              </Typography>
              <Typography variant="h5" mt={0.5}>
                Need a fresh start?
              </Typography>
              <Typography variant="body2" sx={{ color: "#bdc9ed" }} mt={0.5}>
                Fetch new mail, then let the agents do their thing.
              </Typography>
            </Box>
            <TuneRounded
              sx={{ fontSize: 52, color: "#6f8cff", opacity: 0.7 }}
            />
          </Stack>
        </Card>
        <Card sx={{ p: 2.5, minWidth: { md: 310 } }}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Box sx={{ color: "#e86b48" }}>
              <WarningAmberRounded />
            </Box>
            <Box>
              <Typography fontWeight={800}>Review rhythm</Typography>
              <Typography variant="body2" color="text.secondary">
                {stats.review
                  ? `${stats.review} decisions are waiting.`
                  : "No decisions are waiting."}
              </Typography>
            </Box>
          </Stack>
        </Card>
      </Stack>
    </>
  );
}
