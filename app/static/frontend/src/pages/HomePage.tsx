import React, { useEffect, useState } from "react";
import {
    Typography,
    Box,
    Card,
    CardContent,
    Button,
    Grid,
    CircularProgress,
    Alert
} from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { listAnalyses } from "../services/api";
import { Repository } from "../types";


const HomePage: React.FC = () => {
    const [analyses, setAnalyses] = useState<Repository[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchAnalyses() {
            try {
                setLoading(true);
                setError(null);
                const response = await listAnalyses();
                setAnalyses(response.analyses);
            } catch (err: any) {
                setError(err.message || "Unknown error");
            } finally {
                setLoading(false);
            }
        }
        fetchAnalyses();
    }, []);

    return (
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
            {loading && (
                <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
                    <CircularProgress />
                </Box>
            )}
            {error && <Alert severity="error">{error}</Alert>}
            {!loading && !error && analyses.length === 0 && (
                <Alert severity="info">No analyses found. Start by analyzing a repository.</Alert>
            )}
            <Grid container spacing={2}>
                {analyses.map((analysis) => (
                    <Grid item xs={12} md={6} lg={4} key={analysis.repo_id}>
                        <Card variant="outlined">
                            <CardContent>
                                <Typography variant="h6">
                                    {analysis.repo_url.split("/").pop()?.replace(".git", "")}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Status: {analysis.status.charAt(0).toUpperCase() + analysis.status.slice(1)}
                                </Typography>
                                <Button
                                    size="small"
                                    component={RouterLink}
                                    to={`/analysis/${analysis.repo_id}`}
                                    sx={{ mt: 2 }}
                                    variant="outlined"
                                >
                                    View Results
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
};

export default HomePage;
