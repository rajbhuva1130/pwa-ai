import { useState, useCallback, useEffect } from 'react';
import { Chat, Message } from '../types/chat';
import { createNewChat, generateChatTitle, generateResponse, checkHealth } from '../utils/chatUtils';

export const useChat = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  // Initialize with a default chat
  useEffect(() => {
    const defaultChat = createNewChat();
    setChats([defaultChat]);
    setCurrentChatId(defaultChat.id);
    
    // Check backend health
    checkHealth().then(setIsConnected);
  }, []);

  const currentChat = chats.find(chat => chat.id === currentChatId);

  const createChat = useCallback(() => {
    const newChat = createNewChat();
    setChats(prev => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
  }, []);

  const selectChat = useCallback((chatId: string) => {
    setCurrentChatId(chatId);
  }, []);

  const deleteChat = useCallback((chatId: string) => {
    setChats(prev => {
      const filtered = prev.filter(chat => chat.id !== chatId);
      
      // If we deleted the current chat, select the first remaining chat
      if (chatId === currentChatId) {
        if (filtered.length > 0) {
          setCurrentChatId(filtered[0].id);
        } else {
          // If no chats left, create a new one
          const newChat = createNewChat();
          setChats([newChat]);
          setCurrentChatId(newChat.id);
          return [newChat];
        }
      }
      
      return filtered;
    });
  }, [currentChatId]);

  const sendMessage = useCallback(async (content: string) => {
    if (!currentChatId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    // Add user message
    setChats(prev => prev.map(chat => {
      if (chat.id === currentChatId) {
        const updatedMessages = [...chat.messages, userMessage];
        const title = chat.messages.length === 0 ? generateChatTitle(content) : chat.title;
        
        return {
          ...chat,
          messages: updatedMessages,
          title,
          lastMessage: content,
          timestamp: new Date(),
        };
      }
      return chat;
    }));

    setIsLoading(true);

    try {
      // Generate AI response
      const responseContent = await generateResponse(content);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseContent,
        timestamp: new Date(),
      };

      // Add assistant message
      setChats(prev => prev.map(chat => {
        if (chat.id === currentChatId) {
          return {
            ...chat,
            messages: [...chat.messages, assistantMessage],
            lastMessage: responseContent.substring(0, 100),
            timestamp: new Date(),
          };
        }
        return chat;
      }));
    } catch (error) {
      console.error('Error generating response:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm sorry, I encountered an error while processing your message. Please try again.",
        timestamp: new Date(),
      };

      setChats(prev => prev.map(chat => {
        if (chat.id === currentChatId) {
          return {
            ...chat,
            messages: [...chat.messages, errorMessage],
            lastMessage: "Error occurred",
            timestamp: new Date(),
          };
        }
        return chat;
      }));
    } finally {
      setIsLoading(false);
    }
  }, [currentChatId]);

  return {
    chats,
    currentChat,
    currentChatId,
    isLoading,
    isConnected,
    createChat,
    selectChat,
    deleteChat,
    sendMessage,
  };
};