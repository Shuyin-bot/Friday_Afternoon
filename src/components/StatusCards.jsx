import {
  Avatar,
  Box,
  Card,
  CardActionArea,
  Stack,
  Typography,
} from "@mui/material";
import {
  CheckCircleRounded,
  ChevronRightRounded,
  HourglassTopRounded,
  InboxRounded,
  QuestionMarkRounded,
  VisibilityRounded,
} from "@mui/icons-material";

const cardDefinitions = [
  [
    "classification",
    "Needs classification",
    QuestionMarkRounded,
    "#e86b48",
    "#fff0eb",
    "New emails waiting for a first look",
  ],
  [
    "review",
    "Human review",
    VisibilityRounded,
    "#8e5bd9",
    "#f3edff",
    "Decisions waiting for your input",
  ],
  [
    "progress",
    "In progress",
    HourglassTopRounded,
    "#d5961b",
    "#fff7df",
    "Agents currently working",
  ],
  [
    "completed",
    "Completed",
    CheckCircleRounded,
    "#1d9a73",
    "#e8faf3",
    "Quotes successfully prepared",
  ],
  [
    "notQuotation",
    "Not quotation",
    InboxRounded,
    "#718096",
    "#eef1f5",
    "Emails outside the quote workflow",
  ],
];

export function StatusCards({ stats, activeCard, onSelect }) {
  return (
    <Box
      sx={{
        display: "flex",
        gap: 2,
        mb: 4,
        overflowX: "auto",
        pb: 1,
        "&::-webkit-scrollbar": { height: 7 },
        "&::-webkit-scrollbar-thumb": { bgcolor: "#cbd3e1", borderRadius: 5 },
      }}
    >
      {cardDefinitions.map(([key, label, Icon, color, soft, caption]) => (
        <Card
          key={key}
          sx={{
            position: "relative",
            overflow: "hidden",
            flex: { xs: "0 0 272px", md: "1 0 220px" },
            minWidth: { xs: 272, md: 200 },
            border: activeCard === key ? `2px solid ${color}` : undefined,
          }}
        >
          <CardActionArea
            onClick={() => onSelect(activeCard === key ? null : key)}
            sx={{ p: 2.5 }}
          >
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="flex-start"
            >
              <Avatar sx={{ bgcolor: soft, color }}>{<Icon />}</Avatar>
              <ChevronRightRounded sx={{ color: "#b3bbca" }} />
            </Stack>
            <Typography
              color="text.secondary"
              fontSize={13}
              fontWeight={700}
              mt={3}
            >
              {label}
            </Typography>
            <Typography variant="h3" fontSize={42} mt={0.3}>
              {stats[key]}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {caption}
            </Typography>
          </CardActionArea>
          <Box
            sx={{
              height: 4,
              bgcolor: color,
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
            }}
          />
        </Card>
      ))}
    </Box>
  );
}
