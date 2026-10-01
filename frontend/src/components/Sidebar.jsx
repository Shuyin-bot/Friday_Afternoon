import {
  Avatar,
  Box,
  Card,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";
import {
  AutoAwesomeRounded,
  BoltRounded,
  DashboardRounded,
  PsychologyRounded,
} from "@mui/icons-material";

const items = [
  { label: "Overview", icon: <DashboardRounded /> },
  { label: "Human review", icon: <PsychologyRounded /> },
];

export function Sidebar({ onNavigate, activeView }) {
  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Box
        sx={{ px: 3, py: 3.2, display: "flex", alignItems: "center", gap: 1.3 }}
      >
        <Avatar sx={{ bgcolor: "#3155d9", width: 35, height: 35 }}>
          <AutoAwesomeRounded fontSize="small" />
        </Avatar>
        <Box>
          <Typography fontWeight={800} lineHeight={1}>
            Quotely
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Operations desk
          </Typography>
        </Box>
      </Box>
      <Divider />
      <List sx={{ px: 1.5, py: 2 }}>
        {items.map((item) => (
          <ListItem disablePadding key={item.label} sx={{ mb: 0.5 }}>
            <ListItemButton
              selected={item.label === activeView}
              onClick={() => onNavigate(item.label)}
              sx={{
                borderRadius: 2,
                py: 1.2,
                "&.Mui-selected": { bgcolor: "#edf1ff", color: "#3155d9" },
              }}
            >
              <ListItemIcon sx={{ minWidth: 38, color: "inherit" }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{ fontSize: 14, fontWeight: 700 }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Box sx={{ mt: "auto", p: 2 }}>
        <Card sx={{ p: 2, bgcolor: "#f4f6ff", border: 0, boxShadow: "none" }}>
          <BoltRounded sx={{ color: "#3155d9" }} />
          <Typography fontWeight={800} fontSize={13} mt={1}>
            Automation is on
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Incoming emails are being monitored.
          </Typography>
        </Card>
      </Box>
    </Box>
  );
}
