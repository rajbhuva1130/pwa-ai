import { Chat, Message } from '../types/chat';
import { apiRequest, API_ENDPOINTS } from '../config/api';

export const generateChatTitle = (firstMessage: string): string => {
  // Generate a title from the first message (truncate to reasonable length)
  const title = firstMessage.length > 50 
    ? firstMessage.substring(0, 50) + '...' 
    : firstMessage;
  return title;
};

export const createNewChat = (): Chat => {
  const id = Date.now().toString();
  return {
    id,
    title: 'New chat',
    messages: [],
    lastMessage: '',
    timestamp: new Date(),
  };
};

export const generateResponse = async (userMessage: string): Promise<string> => {
  try {
    const formData = new FormData();
    formData.append('prompt', userMessage);

    const response = await apiRequest(API_ENDPOINTS.CHAT, {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    return data.response || 'Sorry, I could not generate a response.';
  } catch (error) {
    console.error('Error calling chat API:', error);
    throw new Error('Failed to get response from the server. Please try again.');
  }
};

export const speechToText = async (audioFile: File): Promise<string> => {
  try {
    const formData = new FormData();
    formData.append('file', audioFile);
    const response = await apiRequest(API_ENDPOINTS.SPEECH_TO_TEXT, {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    return data.text || '';
  } catch (error) {
    console.error('Error calling speech-to-text API:', error);
    throw new Error('Failed to convert speech to text. Please try again.');
  }
};

export const textToSpeech = async (text: string): Promise<string> => {
  try {
    const formData = new FormData();
    formData.append('text', text);
    const response = await apiRequest(API_ENDPOINTS.TEXT_TO_SPEECH, {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    return data.audio_file || '';
  } catch (error) {
    console.error('Error calling text-to-speech API:', error);
    throw new Error('Failed to convert text to speech. Please try again.');
  }
};

export const checkHealth = async (): Promise<boolean> => {
  try {
    const response = await apiRequest(API_ENDPOINTS.HEALTH);
    const data = await response.json();
    return data.status === 'ok';
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};

export const stopProcess = async (): Promise<boolean> => {
  try {
    const response = await apiRequest('/stop', { method: 'POST' });
    const data = await response.json();
    return data.status === 'stopped';
  } catch (error) {
    console.error('Error stopping process:', error);
    return false;
  }
};
