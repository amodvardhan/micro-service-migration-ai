// src/App.tsx
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import RepositoryAnalysisPage from './pages/RepositoryAnalysisPage';
import AnalysisResultsPage from './pages/AnalysisResultsPage';
import ServiceBoundariesPage from './pages/ServiceBoundariesPage';
import NotFoundPage from './pages/NotFoundPage';

const App: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={<Layout />}>
                <Route index element={<HomePage />} />
                <Route path="analyze" element={<RepositoryAnalysisPage />} />
                <Route path="analysis/:repoId" element={<AnalysisResultsPage />} />
                <Route path="services/:repoId" element={<ServiceBoundariesPage />} />
                <Route path="*" element={<NotFoundPage />} />
            </Route>
        </Routes>
    );
};

export default App;
