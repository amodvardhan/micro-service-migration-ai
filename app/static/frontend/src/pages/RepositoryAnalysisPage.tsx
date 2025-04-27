// src/pages/RepositoryAnalysisPage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Typography,
    Box,
    TextField,
    Button,
    Paper,
    CircularProgress,
    Alert,
    Snackbar
} from '@mui/material';
import { analyzeRepository } from '../services/api';

const RepositoryAnalysisPage: React.FC = () => {
    const [repoUrl, setRepoUrl] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [showSnackbar, setShowSnackbar] = useState<boolean>(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!repoUrl) {
            setError('Please enter a repository URL');
            return;
        }

        try {
            setLoading(true);
            setError(null);
            const response = await analyzeRepository(repoUrl);
            setShowSnackbar(true);

            // Navigate to the analysis page after a short delay
            setTimeout(() => {
                navigate(`/analysis/${response.repo_id}`);
            }, 1500);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to analyze repository. Please try again.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box>
            <Typography variant="h4" component="h1" gutterBottom>
                Analyze Repository
            </Typography>
            <Typography variant="body1" paragraph>
                Enter the URL of a Git repository to analyze its structure and identify potential microservice boundaries.
            </Typography>

            <Paper sx={{ p: 3, mt: 3 }}>
                <form onSubmit={handleSubmit}>
                    <TextField
                        label="Repository URL"
                        variant="outlined"
                        fullWidth
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        placeholder="https://github.com/username/repository.git"
                        disabled={loading}
                        error={!!error}
                        helperText={error}
                        sx={{ mb: 3 }}
                    />
                    <Button
                        type="submit"
                        variant="contained"
                        color="primary"
                        size="large"
                        disabled={loading}
                        startIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
                    >
                        {loading ? 'Analyzing...' : 'Analyze Repository'}
                    </Button>
                </form>
            </Paper>

            <Box sx={{ mt: 4 }}>
                <Typography variant="h6" gutterBottom>
                    Example Repositories
                </Typography>
                <Typography variant="body2" paragraph>
                    Try analyzing one of these example repositories:
                </Typography>
                <Box component="ul">
                    <Box component="li">
                        <Button
                            variant="text"
                            onClick={() => setRepoUrl('https://github.com/dotnet-architecture/eShopOnWeb.git')}
                        >
                            eShopOnWeb (.NET)
                        </Button>
                    </Box>
                    <Box component="li">
                        <Button
                            variant="text"
                            onClick={() => setRepoUrl('https://github.com/spring-projects/spring-petclinic.git')}
                        >
                            Spring PetClinic (Java)
                        </Button>
                    </Box>
                    <Box component="li">
                        <Button
                            variant="text"
                            onClick={() => setRepoUrl('https://github.com/gothinkster/realworld.git')}
                        >
                            RealWorld (Various Languages)
                        </Button>
                    </Box>
                </Box>
            </Box>

            <Snackbar
                open={showSnackbar}
                autoHideDuration={3000}
                onClose={() => setShowSnackbar(false)}
            >
                <Alert severity="success" sx={{ width: '100%' }}>
                    Repository analysis started successfully!
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default RepositoryAnalysisPage;
