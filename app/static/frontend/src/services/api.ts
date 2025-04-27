// src/services/api.ts
import axios from 'axios';
import {
    Repository,
    Analysis,
    Service,
    Entity,
    SearchResults,
    ServiceDependency
} from '../types';

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const analyzeRepository = async (repoUrl: string): Promise<{ repo_id: string; repo_url: string; status: string }> => {
    try {
        const response = await api.post('/analyze', { repo_url: repoUrl });
        return response.data;
    } catch (error) {
        console.error('Error analyzing repository:', error);
        throw error;
    }
};

export const getAnalysisResults = async (repoId: string): Promise<Analysis> => {
    try {
        const response = await api.get(`/analysis/${repoId}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching analysis results:', error);
        throw error;
    }
};

export const getServiceBoundaries = async (repoId: string): Promise<{ repo_id: string; repo_url: string; services: Service[] }> => {
    try {
        const response = await api.get(`/services/${repoId}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching service boundaries:', error);
        throw error;
    }
};

export const getServiceDependencies = async (repoId: string): Promise<{
    repo_id: string;
    repo_url: string;
    service_dependencies: Record<string, ServiceDependency[]>
}> => {
    try {
        const response = await api.get(`/dependencies/${repoId}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching service dependencies:', error);
        throw error;
    }
};

export const getEntities = async (repoId: string): Promise<{ repo_id: string; repo_url: string; entities: Entity[] }> => {
    try {
        const response = await api.get(`/entities/${repoId}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching entities:', error);
        throw error;
    }
};

export const searchCode = async (
    query: string,
    topK: number = 5,
    filters: Record<string, any> | null = null
): Promise<SearchResults> => {
    try {
        const response = await api.post('/search', { query, top_k: topK, filters });
        return response.data;
    } catch (error) {
        console.error('Error searching code:', error);
        throw error;
    }
};

export const listAnalyses = async (): Promise<{ analyses: Repository[] }> => {
    try {
        const response = await api.get('/analyses');
        return response.data;
    } catch (error) {
        console.error('Error listing analyses:', error);
        throw error;
    }
};

export default api;
