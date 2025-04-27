// src/pages/ServiceBoundariesPage.tsx
import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
    Typography,
    Box,
    Paper,
    CircularProgress,
    Alert,
    Button,
    Grid,
    Card,
    CardContent,
    CardActions,
    Chip
} from '@mui/material';
import { ForceGraph2D } from 'react-force-graph';
import { getServiceBoundaries, getServiceDependencies } from '../services/api';
import { Service, ServiceDependency, GraphData, GraphNode, GraphLink } from '../types';

const ServiceBoundariesPage: React.FC = () => {
    const { repoId } = useParams<{ repoId: string }>();
    const [services, setServices] = useState<Service[]>([]);
    const [dependencies, setDependencies] = useState<Record<string, ServiceDependency[]>>({});
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
    const graphRef = useRef<any>(null);

    useEffect(() => {
        const fetchData = async () => {
            if (!repoId) return;

            try {
                setLoading(true);

                // Fetch service boundaries
                const servicesData = await getServiceBoundaries(repoId);
                setServices(servicesData.services || []);

                // Fetch service dependencies
                const dependenciesData = await getServiceDependencies(repoId);
                setDependencies(dependenciesData.service_dependencies || {});

                setError(null);
            } catch (err: any) {
                setError(err.response?.data?.detail || 'Failed to fetch service data');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [repoId]);

    useEffect(() => {
        // Prepare graph data when services and dependencies are loaded
        if (services.length > 0) {
            const nodes: GraphNode[] = services.map(service => ({
                id: service.name,
                name: service.name,
                val: (service.entities?.length || 1) * 2, // Size based on number of entities
                color: getRandomColor(service.name)
            }));

            const links: GraphLink[] = [];
            Object.entries(dependencies).forEach(([source, targets]) => {
                targets.forEach(target => {
                    links.push({
                        source,
                        target: target.target,
                        value: 1,
                        type: target.type
                    });
                });
            });

            setGraphData({ nodes, links });
        }
    }, [services, dependencies]);

    const getRandomColor = (str: string): string => {
        // Generate a deterministic color based on the string
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }
        const c = (hash & 0x00FFFFFF)
            .toString(16)
            .toUpperCase();
        return '#' + '00000'.substring(0, 6 - c.length) + c;
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ mt: 2 }}>
                {error}
            </Alert>
        );
    }

    return (
        <Box>
            <Typography variant="h4" component="h1" gutterBottom>
                Service Boundaries
            </Typography>

            <Button
                component={RouterLink}
                to={`/analysis/${repoId}`}
                variant="outlined"
                sx={{ mb: 3 }}
            >
                Back to Analysis
            </Button>

            {services.length === 0 ? (
                <Alert severity="info">
                    No service boundaries identified. The repository may not have clear domain boundaries.
                </Alert>
            ) : (
                <>
                    <Paper sx={{ p: 3, mb: 4 }}>
                        <Typography variant="h6" gutterBottom>
                            Service Dependency Graph
                        </Typography>
                        <Box sx={{ height: '500px', border: '1px solid #eee' }}>
                            {graphData.nodes.length > 0 && (
                                <ForceGraph2D
                                    ref={graphRef}
                                    graphData={graphData}
                                    nodeLabel="name"
                                    nodeRelSize={6}
                                    linkDirectionalArrowLength={3.5}
                                    linkDirectionalArrowRelPos={1}
                                    linkCurvature={0.25}
                                    linkLabel={(link: any) => link.type}
                                    cooldownTicks={100}
                                    onEngineStop={() => graphRef.current?.zoomToFit(400)}
                                />
                            )}
                        </Box>
                    </Paper>

                    <Typography variant="h5" gutterBottom>
                        Identified Services
                    </Typography>

                    <Grid container spacing={3}>
                        {services.map((service) => (
                            <Grid item xs={12} md={6} lg={4} key={service.name}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" component="h3" gutterBottom>
                                            {service.name}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary" paragraph>
                                            {service.description || 'No description available'}
                                        </Typography>

                                        <Typography variant="subtitle2" gutterBottom>
                                            Responsibilities:
                                        </Typography>
                                        <Box sx={{ mb: 2 }}>
                                            {service.responsibilities?.length ? (
                                                service.responsibilities.map((resp) => (
                                                    <Typography key={resp} variant="body2">
                                                        • {resp}
                                                    </Typography>
                                                ))
                                            ) : (
                                                <Typography variant="body2">None specified</Typography>
                                            )}
                                        </Box>

                                        <Typography variant="subtitle2" gutterBottom>
                                            Entities:
                                        </Typography>
                                        <Box sx={{ mb: 1 }}>
                                            {service.entities?.length ? (
                                                service.entities.map((entity) => (
                                                    <Chip
                                                        key={entity}
                                                        label={entity}
                                                        size="small"
                                                        sx={{ mr: 0.5, mb: 0.5 }}
                                                    />
                                                ))
                                            ) : (
                                                <Typography variant="body2">None specified</Typography>
                                            )}
                                        </Box>
                                    </CardContent>
                                    <CardActions>
                                        <Button size="small">View Details</Button>
                                    </CardActions>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                </>
            )}
        </Box>
    );
};

export default ServiceBoundariesPage;
