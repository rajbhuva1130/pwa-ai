import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Mic, MicOff, Square } from 'lucide-react';
import { speechToText } from '../utils/chatUtils';
import { stopProcess } from '../utils/chatUtils';




interface MessageInputProps {
  onSendMessage: (message: string) => void;
  isDarkMode: boolean;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({ 
  onSendMessage, 
  isDarkMode, 
  disabled = false 
}) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];

      recorder.ondataavailable = (event) => {
        chunks.push(event.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
        
        try {
          const transcribedText = await speechToText(audioFile);
          setMessage(prev => prev + (prev ? ' ' : '') + transcribedText);
        } catch (error) {
          console.error('Speech to text error:', error);
        }
        
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      setMediaRecorder(null);
    }
  };

  const [isStopping, setIsStopping] = useState(false);

  const handleStop = async () => {
    setIsStopping(true);
    try {
      const stopped = await stopProcess();
      console.log(stopped ? "Process stopped" : "Failed to stop process");
    } catch (err) {
      console.error(err);
    } finally {
      setIsStopping(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className={`border-t ${isDarkMode ? 'border-gray-800 bg-gray-900' : 'border-gray-200 bg-white'} p-4`}>
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className={`relative flex items-end gap-3 rounded-xl border ${
          isDarkMode 
            ? 'border-gray-700 bg-gray-800' 
            : 'border-gray-300 bg-gray-50'
        } p-3`}>
          
          {/* Attachment button */}
          <button
            type="button"
            disabled={disabled}
            className={`flex-shrink-0 p-2 rounded-lg transition-colors ${
              disabled 
                ? 'opacity-50 cursor-not-allowed'
                : isDarkMode
                  ? 'hover:bg-gray-700 text-gray-400'
                  : 'hover:bg-gray-200 text-gray-500'
            }`}
          >
            <Paperclip size={18} />
          </button>

          {/* Voice recording button */}
          <button
            type="button"
            onClick={toggleRecording}
            disabled={disabled}
            className={`flex-shrink-0 p-2 rounded-lg transition-colors ${
              disabled 
                ? 'opacity-50 cursor-not-allowed'
                : isRecording
                  ? 'bg-red-500 text-white'
                  : isDarkMode
                    ? 'hover:bg-gray-700 text-gray-400'
                    : 'hover:bg-gray-200 text-gray-500'
            }`}
          >
            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          </button>

          {/* Text input */}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Buddy AI..."
            disabled={disabled}
            rows={1}
            className={`flex-1 resize-none border-none outline-none bg-transparent max-h-32 ${
              isDarkMode ? 'text-white placeholder-gray-400' : 'text-gray-900 placeholder-gray-500'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            style={{ minHeight: '24px' }}
          />

          {/* Send button */}
          <button
            type={message.trim() ? "submit" : "button"}
            disabled={disabled || (message.trim() ? !message.trim() : isStopping)}
            onClick={!message.trim() ? handleStop : undefined}
            className={`flex-shrink-0 p-2 rounded-lg transition-colors ${
              disabled
                ? 'opacity-50 cursor-not-allowed'
                : message.trim()
                  ? isDarkMode
                    ? 'bg-white text-gray-900 hover:bg-gray-100'
                    : 'bg-gray-900 text-white hover:bg-gray-800'
                  : 'bg-red-600 text-white hover:bg-red-700'
            }`}
          >
            {message.trim() ? <Send size={18} /> : <Square size={18} />}
          </button>

        </div>
        
        <p className={`text-xs text-center mt-2 ${
          isDarkMode ? 'text-gray-500' : 'text-gray-400'
        }`}>
          Press Enter to send, Shift + Enter for new line{isRecording ? ' • Recording...' : ''}
        </p>
      </form>
    </div>
  );
};