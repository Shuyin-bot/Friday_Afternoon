import { createTheme } from "@mui/material";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#3155d9" },
    secondary: { main: "#e86b48" },
    background: { default: "#f5f7fb", paper: "#ffffff" },
    text: { primary: "#182033", secondary: "#69738a" },
  },
  typography: {
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, sans-serif",
    h3: { fontWeight: 800, letterSpacing: "-.04em" },
    h5: { fontWeight: 800, letterSpacing: "-.03em" },
    button: { textTransform: "none", fontWeight: 700 },
  },
  shape: { borderRadius: 14 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "0 8px 30px rgba(31, 48, 86, .06)",
          border: "1px solid #e8ecf4",
        },
      },
    },
    MuiButton: { defaultProps: { disableElevation: true } },
  },
});
