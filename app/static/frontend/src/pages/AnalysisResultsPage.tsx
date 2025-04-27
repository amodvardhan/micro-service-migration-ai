// src/pages/AnalysisResultsPage.tsx
import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
    Typography,
    Box,
    Paper,
    CircularProgress,
    Alert,
    Tabs,
    Tab,
    Button,
    Chip,
    List,
    ListItem,
    ListItemText,
    Divider
} from '@mui/material';
import { getAnalysisResults } from '../services/api';
import { Analysis, Entity, ApiEndpoint, Service } from '../types';

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`tabpanel-${index}`}
            aria-labelledby={`tab-${index}`}
            {...other}
        >
            {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
        </div>
    );
};

const AnalysisResultsPage: React.FC = () => {
    const { repoId } = useParams<{ repoId: string }>();
    const [analysis, setAnalysis] = useState<Analysis | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [tabValue, setTabValue] = useState<number>(0);
    const pollingIntervalRef = useRef<number | null>(null);

    const fetchAnalysis = async () => {
        if (!repoId) return;

        try {
            const data = await getAnalysisResults(repoId);
            setAnalysis(data);

            // If analysis is complete or failed, stop polling
            if (data.status !== 'processing') {
                if (pollingIntervalRef.current) {
                    window.clearInterval(pollingIntervalRef.current);
                    pollingIntervalRef.current = null;
                }
            }

            setError(null);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to fetch analysis results');
            console.error(err);

            // Stop polling on error
            if (pollingIntervalRef.current) {
                window.clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAnalysis();

        // Set up polling if not already polling
        if (!pollingIntervalRef.current) {
            pollingIntervalRef.current = window.setInterval(fetchAnalysis, 5000);
        }

        // Cleanup function
        return () => {
            if (pollingIntervalRef.current) {
                window.clearInterval(pollingIntervalRef.current);
            }
        };
    }, [repoId]);

    const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
        setTabValue(newValue);
    };

    if (loading && !analysis) {
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

    if (!analysis) {
        return (
            <Alert severity="warning" sx={{ mt: 2 }}>
                No analysis data found
            </Alert>
        );
    }

    if (analysis.status === 'processing') {
        return (
            <Box>
                <Typography variant="h4" component="h1" gutterBottom>
                    Analysis in Progress
                </Typography>
                <Paper sx={{ p: 3, mt: 3, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                    <CircularProgress sx={{ mb: 2 }} />
                    <Typography>
                        Analyzing repository: {analysis.repo_url || 'Unknown repository'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        This may take several minutes depending on the repository size.
                    </Typography>
                </Paper>
            </Box>
        );
    }

    if (analysis.status === 'failed') {
        return (
            <Box>
                <Typography variant="h4" component="h1" gutterBottom>
                    Analysis Failed
                </Typography>
                <Alert severity="error" sx={{ mt: 2 }}>
                    {analysis.error || 'An unknown error occurred during analysis'}
                </Alert>
                <Button
                    component={RouterLink}
                    to="/analyze"
                    variant="contained"
                    sx={{ mt: 3 }}
                >
                    Try Again
                </Button>
            </Box>
        );
    }

    const potentialServices = analysis.analysis?.potential_services || [];
    const entities = analysis.analysis?.entities || [];
    const apiEndpoints = analysis.analysis?.api_endpoints || [];

    return (
        <Box>
            <Typography variant="h4" component="h1" gutterBottom>
                Analysis Results
            </Typography>

            <Paper sx={{ p: 3, mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Repository: {analysis.repo_url}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                    Analyzed on: {new Date(analysis.timestamp).toLocaleString()}
                </Typography>

                <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                        Architecture Type: {analysis.analysis?.architecture_type || 'Unknown'}
                    </Typography>

                    <Button
                        variant="contained"
                        component={RouterLink}
                        to={`/services/${repoId}`}
                        sx={{ mt: 2 }}
                    >
                        View Service Boundaries
                    </Button>
                </Box>
            </Paper>

            <Box sx={{ mt: 4 }}>
                <Tabs value={tabValue} onChange={handleTabChange}>
                    <Tab label="Potential Services" />
                    <Tab label="Entities" />
                    <Tab label="API Endpoints" />
                </Tabs>

                <TabPanel value={tabValue} index={0}>
                    <Typography variant="h6" gutterBottom>
                        Potential Microservices
                    </Typography>
                    {potentialServices.length > 0 ? (
                        <List>
                            {potentialServices.map((service: Service, index: number) => (
                                <React.Fragment key={service.name || index}>
                                    <ListItem>
                                        <ListItemText
                                            primary={service.name}
                                            secondary={
                                                <Box>
                                                    <Typography variant="body2" component="span">
                                                        {service.description || 'No description available'}
                                                    </Typography>
                                                    <Box sx={{ mt: 1 }}>
                                                        {service.entities?.map((entity: string) => (
                                                            <Chip
                                                                key={entity}
                                                                label={entity}
                                                                size="small"
                                                                sx={{ mr: 0.5, mb: 0.5 }}
                                                            />
                                                        ))}
                                                    </Box>
                                                </Box>
                                            }
                                        />
                                    </ListItem>
                                    {index < potentialServices.length - 1 && <Divider />}
                                </React.Fragment>
                            ))}
                        </List>
                    ) : (
                        <Typography>No potential services identified</Typography>
                    )}
                </TabPanel>

                <TabPanel value={tabValue} index={1}>
                    <Typography variant="h6" gutterBottom>
                        Entities
                    </Typography>
                    {entities.length > 0 ? (
                        <List>
                            {entities.map((entity: Entity, index: number) => (
                                <React.Fragment key={entity.name || index}>
                                    <ListItem>
                                        <ListItemText
                                            primary={entity.name}
                                            secondary={
                                                <Box>
                                                    <Typography variant="body2" component="span">
                                                        Type: {entity.type || 'Unknown'}
                                                    </Typography>
                                                    {entity.namespace && (
                                                        <Typography variant="body2" component="div">
                                                            Namespace: {entity.namespace}
                                                        </Typography>
                                                    )}
                                                </Box>
                                            }
                                        />
                                    </ListItem>
                                    {index < entities.length - 1 && <Divider />}
                                </React.Fragment>
                            ))}
                        </List>
                    ) : (
                        <Typography>No entities identified</Typography>
                    )}
                </TabPanel>

                <TabPanel value={tabValue} index={2}>
                    <Typography variant="h6" gutterBottom>
                        API Endpoints
                    </Typography>
                    {apiEndpoints.length > 0 ? (
                        <List>
                            {apiEndpoints.map((endpoint: ApiEndpoint, index: number) => (
                                <React.Fragment key={index}>
                                    <ListItem>
                                        <ListItemText
                                            primary={
                                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                                    <Chip
                                                        label={endpoint.method}
                                                        size="small"
                                                        color={
                                                            endpoint.method === 'GET' ? 'primary' :
                                                                endpoint.method === 'POST' ? 'success' :
                                                                    endpoint.method === 'PUT' ? 'warning' :
                                                                        endpoint.method === 'DELETE' ? 'error' : 'default'
                                                        }
                                                        sx={{ mr: 1 }}
                                                    />
                                                    <Typography component="span">
                                                        {endpoint.route}
                                                    </Typography>
                                                </Box>
                                            }
                                            secondary={endpoint.handler ? `Handler: ${endpoint.handler}` : null}
                                        />
                                    </ListItem>
                                    {index < apiEndpoints.length - 1 && <Divider />}
                                </React.Fragment>
                            ))}
                        </List>
                    ) : (
                        <Typography>No API endpoints identified</Typography>
                    )}
                </TabPanel>
            </Box>
        </Box>
    );
};

export default AnalysisResultsPage;
