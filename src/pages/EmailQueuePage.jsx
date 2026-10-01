import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Box,
  Button,
  Chip,
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
import { filterJobsByCard, filterJobsBySearch } from "../utils/jobFilters";

const filterChips = [
  { key: null, label: "All" },
  { key: "classification", label: "Needs classification" },
  { key: "progress", label: "In progress" },
  { key: "review", label: "Human review" },
  { key: "completed", label: "Completed" },
  { key: "notQuotation", label: "Not quotation" },
];

export function EmailQueuePage({ onOpenJob, onNotice }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeChip, setActiveChip] = useState(null);
  const [search, setSearch] = useState("");
  const [busyAction, setBusyAction] = useState("");

  const loadJobs = useCallback(async () => {
    try {
      const jobsData = await jobService.getJobs();
      setJobs(mapJobs(jobsData));
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
      onNotice("Fetch emails started successfully.");
    } catch {
      onNotice("Could not reach the API. Fetch emails is ready once the backend is running.");
    } finally {
      setBusyAction("");
    }
  }

  const counts = useMemo(() => {
    const result = {};
    filterChips.forEach(({ key }) => {
      result[key ?? "all"] = key ? filterJobsByCard(jobs, key).length : jobs.length;
    });
    return result;
  }, [jobs]);

  const visibleJobs = useMemo(() => {
    const byCard = filterJobsByCard(jobs, activeChip);
    return filterJobsBySearch(byCard, search);
  }, [jobs, activeChip, search]);

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
            Email queue
          </Typography>
          <Typography color="text.secondary" mt={1}>
            Every inbound email moving through the quotation pipeline.
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

      <Stack
        direction={{ xs: "column", md: "row" }}
        spacing={2}
        alignItems={{ xs: "stretch", md: "center" }}
        justifyContent="space-between"
        mb={3}
      >
        <Box
          sx={{
            display: "flex",
            gap: 1,
            flexWrap: "wrap",
            overflowX: { xs: "auto", md: "visible" },
          }}
        >
          {filterChips.map(({ key, label }) => (
            <Chip
              key={label}
              label={`${label} · ${counts[key ?? "all"] ?? 0}`}
              onClick={() => setActiveChip(key)}
              color={activeChip === key ? "primary" : "default"}
              variant={activeChip === key ? "filled" : "outlined"}
              sx={{ fontWeight: 700 }}
            />
          ))}
        </Box>
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
              ? filterChips.find((chip) => chip.key === activeChip)?.label
              : "All queued emails"
          }
          subtitle="Click a job to open its review workspace."
          onRefresh={loadJobs}
          onOpen={onOpenJob}
        />
      )}
    </>
  );
}
