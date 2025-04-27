// src/pages/NotFoundPage.tsx
import React from 'react';
import { Typography, Box, Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const NotFoundPage: React.FC = () => {
    return (
        <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h2" component="h1" gutterBottom>
                404
            </Typography>
            <Typography variant="h5" component="h2" gutterBottom>
                Page Not Found
            </Typography>
            <Typography variant="body1" paragraph>
                The page you are looking for doesn't exist or has been moved.
            </Typography>
            <Button variant="contained" component={RouterLink} to="/">
                Go to Home
            </Button>
        </Box>
    );
};

export default NotFoundPage;
