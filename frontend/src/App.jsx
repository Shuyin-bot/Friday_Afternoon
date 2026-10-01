import { useState } from "react";
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  Snackbar,
  Toolbar,
  Typography,
} from "@mui/material";
import { MenuRounded } from "@mui/icons-material";
import { ThemeProvider } from "@mui/material/styles";
import { Sidebar } from "./components/Sidebar";
import { DashboardPage } from "./pages/DashboardPage";
import { EmailQueuePage } from "./pages/EmailQueuePage";
import { JobDetailPage } from "./pages/JobDetailPage";
import { theme } from "./theme";

const drawerWidth = 248;

function App() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activeView, setActiveView] = useState("Overview");
  const [selectedJob, setSelectedJob] = useState(null);
  const [notice, setNotice] = useState("");

  function navigate(label) {
    setActiveView(label);
    setSelectedJob(null);
    setMobileOpen(false);
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: "flex", minHeight: "100vh" }}>
        <AppBar
          position="fixed"
          color="inherit"
          elevation={0}
          sx={{
            display: { xs: "flex", md: "none" },
            borderBottom: "1px solid #e8ecf4",
          }}
        >
          <Toolbar>
            <IconButton onClick={() => setMobileOpen(!mobileOpen)}>
              <MenuRounded />
            </IconButton>
            <Typography fontWeight={800}>Quotely</Typography>
          </Toolbar>
        </AppBar>
        <Box
          component="nav"
          sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
        >
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={() => setMobileOpen(false)}
            ModalProps={{ keepMounted: true }}
            sx={{
              display: { xs: "block", md: "none" },
              "& .MuiDrawer-paper": { width: drawerWidth },
            }}
          >
            <Sidebar onNavigate={navigate} activeView={activeView} />
          </Drawer>
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: "none", md: "block" },
              "& .MuiDrawer-paper": {
                width: drawerWidth,
                boxSizing: "border-box",
                borderRight: "1px solid #e8ecf4",
              },
            }}
            open
          >
            <Sidebar onNavigate={navigate} activeView={activeView} />
          </Drawer>
        </Box>
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            pt: { xs: 10, md: 0 },
            px: { xs: 2, sm: 4, lg: 7 },
            py: { xs: 3, md: 6 },
            maxWidth: 1440,
            mx: "auto",
            width: "100%",
          }}
        >
          {selectedJob ? (
            <JobDetailPage
              job={selectedJob}
              onBack={() => setSelectedJob(null)}
              onNotice={setNotice}
            />
          ) : activeView === "Human review" ? (
            <EmailQueuePage
              pageTitle="Human Review"
              onOpenJob={setSelectedJob}
              onNotice={setNotice}
            />
          ) : (
            <DashboardPage onOpenJob={setSelectedJob} onNotice={setNotice} />
          )}
        </Box>
        <Snackbar
          open={Boolean(notice)}
          autoHideDuration={4500}
          onClose={() => setNotice("")}
          message={notice}
        />
      </Box>
    </ThemeProvider>
  );
}

export default App;
