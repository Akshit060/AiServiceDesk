const API_BASE = 'http://localhost:8000/api';

async function request(url, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed (${response.status})`);
    }
    return await response.json();
  } catch (error) {
    if (error.message === 'Failed to fetch') {
      throw new Error('Cannot connect to the server. Please ensure the backend is running.');
    }
    throw error;
  }
}

// Dashboard
export const fetchDashboard = () => request('/dashboard');

// Tickets
export const fetchTickets = (params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== '') query.append(key, val);
  });
  return request(`/tickets?${query.toString()}`);
};
export const fetchTicket = (id) => request(`/tickets/${id}`);
export const createTicket = (data) => request('/tickets', { method: 'POST', body: JSON.stringify(data) });
export const updateTicket = (id, data) => request(`/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(data) });

// Comments
export const fetchComments = (ticketId) => request(`/tickets/${ticketId}/comments`);
export const addComment = (ticketId, data) => request(`/tickets/${ticketId}/comments`, { method: 'POST', body: JSON.stringify(data) });

// AI
export const analyzeTicket = (ticketId) => request(`/tickets/${ticketId}/analyze`, { method: 'POST' });
export const classifyTicket = (data) => request('/tickets/classify', { method: 'POST', body: JSON.stringify(data) });
export const fetchRelatedTickets = (ticketId) => request(`/tickets/${ticketId}/related`);
export const generateResolutionDraft = (ticketId) => request(`/tickets/${ticketId}/generate-resolution`, { method: 'POST' });
export const chatAboutTicket = (ticketId, data) => request(`/tickets/${ticketId}/chat`, { method: 'POST', body: JSON.stringify(data) });
export const rebuildEmbeddings = () => request('/embeddings/rebuild', { method: 'POST' });

// Knowledge Base
export const fetchKnowledgeBase = (params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== '') query.append(key, val);
  });
  return request(`/knowledge-base?${query.toString()}`);
};

// Agents & Categories
export const fetchAgents = () => request('/agents');
export const fetchCategories = () => request('/categories');
