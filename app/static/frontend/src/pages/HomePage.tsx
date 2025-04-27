// src/pages/HomePage.tsx
import React, { useState, useEffect } from 'react';
import { Typography, Box, Card, CardContent, Button, Grid, CircularProgress } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { listAnalyses } from '../services/api';
import { Repository } from '../types';

const HomePage: React.FC = () => {
    const [analyses, setAnalyses] = useState<Repository[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAnalyses = async () => {
            try {
                setLoading(true);
                const response = await listAnalyses();
                setAnalyses(response.analyses || []);
                setError(null);
            } catch (err) {
                setError('Failed to load analyses. Please try again later.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchAnalyses();
    }, []);

    return (
        <Box>
            <Box sx={{ textAlign: 'center', mb: 6 }}>
                <Typography variant="h2" component="h1" gutterBottom>
                    Microservice Migration AI
                </Typography>
                <Typography variant="h5" component="h2" color="text.secondary" paragraph>
                    An AI-powered tool for migrating monolithic applications to microservices
                </Typography>
                <Button
                    variant="contained"
                    color="primary"
                    size="large"
                    component={RouterLink}
                    to="/analyze"
                    sx={{ mt: 2 }}
                >
                    Analyze Repository
                </Button>
            </Box>

            <Box sx={{ mt: 6 }}>
                <Typography variant="h4" component="h2" gutterBottom>
                    Recent Analyses
                </Typography>
                {loading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                        <CircularProgress />
                    </Box>
                ) : error ? (
                    <Typography color="error">{error}</Typography>
                ) : analyses.length === 0 ? (
                    <Typography>No analyses found. Start by analyzing a repository.</Typography>
                ) : (
                    <Grid container spacing={3}>
                        {analyses.map((analysis) => (
                            <Grid item xs={12} md={6} key={analysis.repo_id}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" component="h3" gutterBottom>
                                            {analysis.repo_url.split('/').pop()}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary" gutterBottom>
                                            {analysis.repo_url}
                                        </Typography>
                                        <Typography variant="body2" gutterBottom>
                                            Status: {analysis.status}
                                        </Typography>
                                        <Typography variant="body2" gutterBottom>
                                            Analyzed: {new Date(analysis.timestamp).toLocaleString()}
                                        </Typography>
                                        <Button
                                            variant="outlined"
                                            component={RouterLink}
                                            to={`/analysis/${analysis.repo_id}`}
                                            sx={{ mt: 2 }}
                                            disabled={analysis.status !== 'completed'}
                                        >
                                            View Results
                                        </Button>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                )}
            </Box>
        </Box>
    );
};

export default HomePage;
