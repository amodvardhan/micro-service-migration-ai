import React from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import RepositoryAnalysisPage from "./pages/RepositoryAnalysisPage";
import NotFoundPage from "./pages/NotFoundPage";
import AnalysisResultsPage from "./pages/AnalysisResultsPage";

const App: React.FC = () => (
    <Routes>
        <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="analyze" element={<RepositoryAnalysisPage />} />
            <Route path="analysis/:repoId" element={<AnalysisResultsPage />} />
            <Route path="*" element={<NotFoundPage />} />
        </Route>
    </Routes>
);

export default App;
