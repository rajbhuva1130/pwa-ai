import React from 'react';
import { User, Bot, Volume2 } from 'lucide-react';
import { textToSpeech } from '../utils/chatUtils';

interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
  };
  isDarkMode: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isDarkMode }) => {
  const isUser = message.role === 'user';

  const handlePlayAudio = async () => {
    try {
      const audioPath = await textToSpeech(message.content);
      // In a real implementation, you would play the audio file
      // For now, we'll just log the path
      console.log('Audio file path:', audioPath);
      
      // You could implement audio playback here:
      // const audio = new Audio(audioPath);
      // audio.play();
    } catch (error) {
      console.error('Error playing audio:', error);
    }
  };
  return (
    <div className={`group relative flex gap-4 p-6 ${
      isDarkMode 
        ? isUser ? 'bg-gray-800' : 'bg-gray-900' 
        : isUser ? 'bg-gray-50' : 'bg-white'
    }`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser 
          ? isDarkMode ? 'bg-blue-600' : 'bg-blue-500'
          : isDarkMode ? 'bg-green-600' : 'bg-green-500'
      }`}>
        {isUser ? (
          <User size={16} className="text-white" />
        ) : (
          <Bot size={16} className="text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className="flex-1 min-w-0">
        <div className={`font-medium text-sm mb-1 ${
          isDarkMode ? 'text-gray-300' : 'text-gray-600'
        }`}>
          {isUser ? 'You' : 'Assistant'}
        </div>
        
        <div className={`prose max-w-none ${
          isDarkMode 
            ? 'prose-invert text-gray-100' 
            : 'text-gray-900'
        }`}>
          <p className="whitespace-pre-wrap leading-relaxed">
            {message.content}
          </p>
        </div>

        <div className={`flex items-center justify-between mt-2`}>
          <div className={`text-xs ${
            isDarkMode ? 'text-gray-500' : 'text-gray-400'
          }`}>
            {message.timestamp.toLocaleTimeString()}
          </div>
          
          {!isUser && (
            <button
              onClick={handlePlayAudio}
              className={`p-1 rounded transition-colors ${
                isDarkMode 
                  ? 'hover:bg-gray-700 text-gray-400 hover:text-gray-300' 
                  : 'hover:bg-gray-100 text-gray-500 hover:text-gray-600'
              }`}
              title="Play audio"
            >
              <Volume2 size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};