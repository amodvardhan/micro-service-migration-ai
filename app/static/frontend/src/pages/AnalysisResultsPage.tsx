// src/pages/AnalysisResultsPage.tsx

import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
    Typography, Box, Paper, CircularProgress, Alert, Tabs, Tab, Button, Chip,
    List, ListItem, ListItemText, Divider
} from '@mui/material';
import { getAnalysisResults } from '../services/api';
import { Entity, ApiEndpoint, Service } from '../types';

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => (
    <div role="tabpanel" hidden={value !== index} {...other}>
        {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
);

const AnalysisResultsPage: React.FC = () => {
    const { repoId } = useParams<{ repoId: string }>();
    const [analysis, setAnalysis] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [tabValue, setTabValue] = useState(0);
    const pollingIntervalRef = useRef<number | null>(null);

    const fetchAnalysis = async () => {
        if (!repoId) return;
        try {
            const data = await getAnalysisResults(repoId);
            setAnalysis(data);
            if (data.status !== 'processing' && pollingIntervalRef.current) {
                window.clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
            setError(null);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to fetch analysis results');
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
        if (!pollingIntervalRef.current) {
            pollingIntervalRef.current = window.setInterval(fetchAnalysis, 5000);
        }
        return () => {
            if (pollingIntervalRef.current) {
                window.clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
        };
        // eslint-disable-next-line
    }, [repoId]);

    const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => setTabValue(newValue);

    if (loading && !analysis) return <CircularProgress />;
    if (error) return <Alert severity="error">{error}</Alert>;
    if (!analysis) return <Alert severity="info">No analysis data found</Alert>;
    if (analysis.status === 'processing') {
        return (
            <Box sx={{ mt: 4 }}>
                <Typography variant="h5">Analysis in Progress</Typography>
                <Typography>Analyzing repository: {analysis.repo_url || 'Unknown repository'}</Typography>
                <Typography>This may take several minutes depending on the repository size.</Typography>
                <CircularProgress sx={{ mt: 2 }} />
            </Box>
        );
    }
    if (analysis.status === 'failed') {
        return (
            <Box sx={{ mt: 4 }}>
                <Alert severity="error">Analysis Failed</Alert>
                <Typography>{analysis.error || 'An unknown error occurred during analysis'}</Typography>
                <Button variant="contained" color="primary" sx={{ mt: 2 }} component={RouterLink} to="/">
                    Try Again
                </Button>
            </Box>
        );
    }

    const potentialServices = analysis.analysis?.potential_services || [];
    const entities = analysis.analysis?.entities || [];
    const apiEndpoints = analysis.analysis?.api_endpoints || [];
    const developerOutputs = analysis.analysis?.developer_outputs || [];

    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Analysis Results
            </Typography>
            <Typography variant="subtitle1" gutterBottom>
                Repository: {analysis.repo_url}
            </Typography>
            <Typography variant="subtitle2" gutterBottom>
                Analyzed on: {new Date(analysis.timestamp).toLocaleString()}
            </Typography>
            <Typography variant="subtitle2" gutterBottom>
                Architecture Type: {analysis.analysis?.architecture_type || 'Unknown'}
            </Typography>
            <Box sx={{ my: 2 }}>
                <Button
                    variant="outlined"
                    color="primary"
                    component={RouterLink}
                    to={`/services/${repoId}`}
                >
                    View Service Boundaries
                </Button>
            </Box>
            <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label="Potential Services" />
                <Tab label="Entities" />
                <Tab label="API Endpoints" />
                <Tab label="Generated Microservices" />
            </Tabs>

            {/* Potential Services */}
            <TabPanel value={tabValue} index={0}>
                <Typography variant="h6" gutterBottom>
                    Potential Microservices
                </Typography>
                {potentialServices.length > 0 ? (
                    <List>
                        {potentialServices.map((service: Service, index: number) => (
                            <React.Fragment key={index}>
                                <ListItem alignItems="flex-start">
                                    <ListItemText
                                        primary={service.name}
                                        secondary={service.description || 'No description available'}
                                    />
                                    <Box sx={{ ml: 2 }}>
                                        <Typography variant="caption">Entities:</Typography>
                                        {service.entities?.length ? (
                                            service.entities.map((entity: string, i: number) => (
                                                <Chip key={i} label={entity} size="small" sx={{ ml: 0.5 }} />
                                            ))
                                        ) : (
                                            <Chip label="None" size="small" sx={{ ml: 0.5 }} />
                                        )}
                                    </Box>
                                </ListItem>
                                {index < potentialServices.length - 1 && <Divider />}
                            </React.Fragment>
                        ))}
                    </List>
                ) : (
                    <Typography>No potential services identified</Typography>
                )}
            </TabPanel>

            {/* Entities */}
            <TabPanel value={tabValue} index={1}>
                <Typography variant="h6" gutterBottom>
                    Entities
                </Typography>
                {entities.length > 0 ? (
                    <List>
                        {entities.map((entity: Entity, index: number) => (
                            <React.Fragment key={index}>
                                <ListItem>
                                    <ListItemText
                                        primary={entity.name}
                                        secondary={`Type: ${entity.type || 'Unknown'}${entity.namespace ? ` | Namespace: ${entity.namespace}` : ''}`}
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

            {/* API Endpoints */}
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
                                        primary={endpoint.route}
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

            {/* Generated Microservices */}
            <TabPanel value={tabValue} index={3}>
                <Typography variant="h6" gutterBottom>
                    Generated Microservices
                </Typography>
                {developerOutputs.length > 0 ? (
                    developerOutputs.map((svc: any, idx: number) => (
                        <Box key={idx} sx={{ mb: 4 }}>
                            <Typography variant="subtitle1">{svc.service_name}</Typography>
                            <List>
                                {svc.files.map((file: any, fidx: number) => (
                                    <React.Fragment key={fidx}>
                                        <ListItem alignItems="flex-start">
                                            <ListItemText
                                                primary={file.path}
                                                secondary={
                                                    <Box sx={{ mt: 1 }}>
                                                        <Paper variant="outlined" sx={{ p: 2, bgcolor: "#f9f9f9" }}>
                                                            <pre style={{ margin: 0, fontSize: "0.9em", maxHeight: 300, overflow: "auto" }}>
                                                                {file.content.length > 1000
                                                                    ? file.content.slice(0, 1000) + "\n...[truncated]"
                                                                    : file.content}
                                                            </pre>
                                                        </Paper>
                                                    </Box>
                                                }
                                            />
                                        </ListItem>
                                        {fidx < svc.files.length - 1 && <Divider />}
                                    </React.Fragment>
                                ))}
                            </List>
                        </Box>
                    ))
                ) : (
                    <Typography>No microservice code generated yet.</Typography>
                )}
            </TabPanel>
        </Box>
    );
};

export default AnalysisResultsPage;
