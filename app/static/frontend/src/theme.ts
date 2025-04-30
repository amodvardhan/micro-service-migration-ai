// src/theme.ts
import { createTheme } from "@mui/material/styles";

const theme = createTheme({
    palette: {
        primary: { main: "#1976d2" },
        secondary: { main: "#009688" },
        background: { default: "#f4f6fa" },
    },
    shape: { borderRadius: 8 },
    typography: {
        fontFamily: "Inter, Roboto, Arial, sans-serif",
        h4: { fontWeight: 700 },
        h6: { fontWeight: 600 },
    },
});

export default theme;
