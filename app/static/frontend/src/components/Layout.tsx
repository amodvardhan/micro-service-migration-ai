import React from "react";
import { Outlet, Link as RouterLink, useLocation } from "react-router-dom";
import { AppBar, Toolbar, Typography, Button, Container, Box, CssBaseline } from "@mui/material";
import { ThemeProvider } from "@mui/material/styles";
import theme from "../theme";

const Layout: React.FC = () => {
    const location = useLocation();

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <AppBar position="static" color="primary" elevation={2}>
                <Toolbar>
                    <Typography variant="h6" sx={{ flexGrow: 1 }}>
                        <Button
                            component={RouterLink}
                            to="/"
                            color="inherit"
                            sx={{ fontWeight: 700, fontSize: "1.2rem" }}
                        >
                            Microservice Migration AI
                        </Button>
                    </Typography>
                    <Button
                        color="inherit"
                        component={RouterLink}
                        to="/analyze"
                        sx={{
                            borderBottom:
                                location.pathname === "/analyze" ? "2px solid #fff" : "none",
                        }}
                    >
                        Analyze
                    </Button>
                    <Button
                        color="inherit"
                        component={RouterLink}
                        to="/"
                        sx={{
                            borderBottom:
                                location.pathname === "/" ? "2px solid #fff" : "none",
                        }}
                    >
                        Dashboard
                    </Button>
                </Toolbar>
            </AppBar>
            <Container sx={{ py: 4 }}>
                <Outlet />
            </Container>
            <Box sx={{ py: 2, textAlign: "center", color: "grey.600" }}>
                <Typography variant="body2">
                    &copy; {new Date().getFullYear()} Microservice Migration AI
                </Typography>
            </Box>
        </ThemeProvider>
    );
};

export default Layout;
