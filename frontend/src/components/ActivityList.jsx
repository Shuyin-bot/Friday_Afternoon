import { useState } from "react";
import {
  Avatar,
  Box,
  Card,
  Chip,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Pagination,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  CheckCircleRounded,
  EmailRounded,
  RefreshRounded,
} from "@mui/icons-material";
import { getStatusVisual } from "../utils/statusStyles";

export function ActivityList({
  jobs,
  title,
  subtitle,
  onRefresh,
  onOpen,
  showIndex = false,
}) {
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const pageCount = Math.max(1, Math.ceil(jobs.length / pageSize));
  const visibleJobs = jobs.slice((page - 1) * pageSize, page * pageSize);

  return (
    <Card sx={{ p: { xs: 2, md: 3 }, mb: 3 }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Box>
          <Typography variant="h5">{title}</Typography>
          <Typography color="text.secondary" variant="body2" mt={0.5}>
            {subtitle}
          </Typography>
        </Box>
        <Tooltip title="Refresh dashboard">
          <IconButton onClick={onRefresh}>
            <RefreshRounded />
          </IconButton>
        </Tooltip>
      </Stack>
      <Divider />
      <List disablePadding>
        {jobs.length ? (
          visibleJobs.map((job, index) => (
            <ListItem
              key={job.id}
              disableGutters
              divider={index < visibleJobs.length - 1}
              secondaryAction={
                (() => {
                  const { color, soft } = getStatusVisual(job.status);
                  return (
                    <Chip
                      label={job.status}
                      size="small"
                      sx={{
                        bgcolor: soft,
                        color,
                        border: `1px solid ${color}33`,
                        fontWeight: 800,
                      }}
                    />
                  );
                })()
              }
            >
              {showIndex && (
                <Box
                  sx={{
                    width: 38,
                    flexShrink: 0,
                    textAlign: "center",
                    color: "text.secondary",
                    fontSize: 12,
                    fontWeight: 800,
                  }}
                >
                  #{(page - 1) * pageSize + index + 1}
                </Box>
              )}
              <ListItemButton
                onClick={() => onOpen(job)}
                sx={{ borderRadius: 2, py: 1.2 }}
              >
                <ListItemIcon>
                  <Avatar
                    sx={{
                      bgcolor: "#f0f3fa",
                      color: "#52627e",
                      width: 38,
                      height: 38,
                    }}
                  >
                    <EmailRounded fontSize="small" />
                  </Avatar>
                </ListItemIcon>
                <ListItemText
                  primary={job.title}
                  secondary={`${job.sender}  •  ${job.time}`}
                  primaryTypographyProps={{ fontWeight: 750, fontSize: 14 }}
                  secondaryTypographyProps={{ fontSize: 12 }}
                />
              </ListItemButton>
            </ListItem>
          ))
        ) : (
          <Box sx={{ py: 7, textAlign: "center" }}>
            <CheckCircleRounded sx={{ color: "#1d9a73", fontSize: 42 }} />
            <Typography fontWeight={800} mt={1}>
              Nothing needs your attention
            </Typography>
            <Typography variant="body2" color="text.secondary">
              You’re all caught up in this queue.
            </Typography>
          </Box>
        )}
      </List>
      {pageCount > 1 && (
        <Stack alignItems="center" mt={2.5}>
          <Pagination
            count={pageCount}
            page={page}
            onChange={(_, nextPage) => setPage(nextPage)}
            color="primary"
            size="small"
            shape="rounded"
          />
        </Stack>
      )}
    </Card>
  );
}
