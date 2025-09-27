// API Configuration
// export const API_BASE_URL = 'http://localhost:8000'; // Update this to your backend URL
export const API_BASE_URL = 'http://192.168.0.22:8000';


export const API_ENDPOINTS = {
  HEALTH: '/health',
  CHAT: '/chat',
  SPEECH_TO_TEXT: '/stt',
  TEXT_TO_SPEECH: '/tts',
} as const;

// API utility functions
export const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response;
  } catch (error) {
    console.error('API request error:', error);
    throw error;
  }
};