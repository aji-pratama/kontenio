import axios from 'axios';
import { VideoProject, VideoSegment, AnalyzeResponse, RenderResponse } from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';

const client = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const api = {
    getProjects: async (): Promise<VideoProject[]> => {
        const response = await client.get('/projects');
        return response.data;
    },

    getProject: async (id: number): Promise<VideoProject> => {
        const response = await client.get(`/projects/${id}`);
        return response.data;
    },

    createProject: async (title: string, file: File): Promise<VideoProject> => {
        const formData = new FormData();
        formData.append('title', title);
        formData.append('video_file', file);

        const response = await client.post('/projects', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    analyzeProject: async (projectId: number): Promise<AnalyzeResponse> => {
        const response = await client.post(`/projects/${projectId}/analyze`);
        return response.data;
    },

    getSegments: async (projectId: number): Promise<VideoSegment[]> => {
        const response = await client.get(`/projects/${projectId}/segments`);
        return response.data;
    },

    updateSegment: async (segmentId: number, data: Partial<VideoSegment>) => {
        const response = await client.patch(`/segments/${segmentId}`, data);
        return response.data;
    },

    renderProject: async (projectId: number): Promise<RenderResponse> => {
        const response = await client.post(`/projects/${projectId}/render`);
        return response.data;
    },
};
