// src/pages/HomePage.tsx
import React from "react";
import {
    Typography,
    Box,
    Card,
    CardContent,
    Button,
    Grid
} from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

const HomePage: React.FC = () => (
    <Box>
        <Typography variant="h4" component="h1" gutterBottom>
            Welcome to Microservice Migration AI
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
            Seamlessly modernize your legacy monoliths into scalable microservices using AI.
        </Typography>
        <Box sx={{ my: 4 }}>
            <Button
                variant="contained"
                color="primary"
                size="large"
                component={RouterLink}
                to="/analyze"
            >
                Start New Analysis
            </Button>
        </Box>
        <Typography variant="h5" gutterBottom>
            Recent Analyses
        </Typography>
        {/* Replace with a Table or Card Grid for real data */}
        <Grid container spacing={2}>
            {/* Example card */}
            <Grid item xs={12} md={6} lg={4}>
                <Card variant="outlined">
                    <CardContent>
                        <Typography variant="h6">eShopOnWeb</Typography>
                        <Typography variant="body2" color="text.secondary">
                            Status: Completed
                        </Typography>
                        <Button
                            size="small"
                            component={RouterLink}
                            to="/analysis/123"
                            sx={{ mt: 2 }}
                            variant="outlined"
                        >
                            View Results
                        </Button>
                    </CardContent>
                </Card>
            </Grid>
        </Grid>
    </Box>
);

export default HomePage;
