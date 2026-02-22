import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const analyzeSample = async (antibiotic, genePresence) => {
    try {
        const response = await api.post('/prediction/analyze', {
            antibiotic: antibiotic,
            gene_presence: genePresence
        });
        return response.data;
    } catch (error) {
        console.error('Analysis API Error:', error);
        throw error;
    }
};

export const uploadFasta = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await api.post('/prediction/upload_fasta', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        console.error('FASTA Upload Error:', error);
        throw error;
    }
};

export const getMapData = async (mapType, antibiotic = null) => {
    try {
        const params = antibiotic ? { antibiotic } : {};
        const response = await api.get(`/maps/${mapType}`, { params });
        return response.data;
    } catch (error) {
        console.warn(`Map data for ${mapType} unavailable.`);
        return { status: "unavailable", message: "Data unavailable", data: [] };
    }
};

export const getTrendsData = async (filters = {}) => {
    try {
        const response = await api.get('/maps/analytics/trends', { params: filters });
        return response.data;
    } catch (error) {
        console.error("Failed to fetch trends", error);
        return { labels: [], datasets: [] };
    }
};

export const getAntibiotics = async () => {
    try {
        const response = await api.get('/maps/antibiotics');
        return response.data.antibiotics || [];
    } catch (error) {
        console.error("Failed to fetch antibiotics", error);
        return [];
    }
};

export const getHeatmapData = async () => {
    try {
        const response = await api.get('/maps/analytics/heatmap');
        return response.data;
    } catch (error) {
        console.error("Failed to fetch heatmap", error);
        return { x_labels: [], y_labels: [], data: [] };
    }
};
