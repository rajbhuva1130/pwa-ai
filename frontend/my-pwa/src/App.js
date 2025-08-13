import React, { useState, useEffect, useRef, useCallback } from "react";
import "./App.css";
import { FaPaperPlane, FaMicrophone, FaStop } from "react-icons/fa";

// Check for Web Speech API browser support
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

const recognition = SpeechRecognition ? new SpeechRecognition() : null;

// Configure recognition settings
if (recognition) {
  recognition.continuous = false; // Stop listening after one utterance
  recognition.lang = "en-US";
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("Idle");
  const [isListening, setIsListening] = useState(false);
  const chatRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  const speakResponse = useCallback((text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onstart = () => setStatus("Speaking...");
    utterance.onend = () => setStatus("Idle");
    window.speechSynthesis.speak(utterance);
  }, []);

  const sendMessage = useCallback(
    async (messageText = input) => {
      if (!messageText.trim()) return;

      // Add user message to state
      setMessages((prev) => [...prev, { text: messageText, sender: "user" }]);
      setInput("");
      setStatus("Typing...");

      try {
        const formData = new FormData();
        formData.append("prompt", messageText);

        const res = await fetch("http://127.0.0.1:8000/chat", {
          method: "POST",
          body: formData,
        });

        const data = await res.json();
        setMessages((prev) => [...prev, { text: data.response, sender: "bot" }]);
        speakResponse(data.response); // Use voice for the bot's response
      } catch (error) {
        setMessages((prev) => [
          ...prev,
          { text: "⚠ Could not connect to backend.", sender: "bot" },
        ]);
        setStatus("Error");
      }
    },
    [input, setMessages, setStatus, speakResponse]
  );

  // Set up speech recognition event handlers
  useEffect(() => {
    if (!recognition) {
      setStatus("Voice command not supported");
      return;
    }

    recognition.onstart = () => {
      setStatus("Listening...");
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      sendMessage(transcript);
    };

    recognition.onend = () => {
      setStatus("Idle");
      setIsListening(false);
    };

    recognition.onerror = (event) => {
      setStatus("Error: " + event.error);
      setIsListening(false);
    };

    return () => {
      recognition.onstart = null;
      recognition.onresult = null;
      recognition.onend = null;
      recognition.onerror = null;
    };
  }, [sendMessage]);

  const toggleListening = () => {
    if (!recognition) return;
    if (isListening) {
      recognition.stop();
    } else {
      setInput(""); // Clear input field before listening
      recognition.start();
    }
  };

  return (
    <div className="chatgpt-container">
      <div className="chatgpt-main">
        {/* Chat window */}
        <div className="chat-window" ref={chatRef}>
          {messages.length === 0 ? (
            <div className="initial-screen">
              <p className="welcome-text">How can I help you today?</p>
              <div className="voice-cta">
                <p>Tap the microphone to start talking.</p>
                <button
                  className={`voice-button ${isListening ? "active" : ""}`}
                  onClick={toggleListening}
                >
                  {isListening ? <FaStop /> : <FaMicrophone />}
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className={`message-bubble ${msg.sender}`}>
                <div className="message-content">
                  <p>{msg.text}</p>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input area */}
        <div className="input-container">
          <button
            className={`voice-button ${isListening ? "active" : ""}`}
            onClick={toggleListening}
          >
            {isListening ? <FaStop /> : <FaMicrophone />}
          </button>
          <input
            type="text"
            placeholder="Send a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button onClick={() => sendMessage()} disabled={!input.trim()}>
            <FaPaperPlane />
          </button>
        </div>
        <div className="status-container">
          <p>{status}</p>
        </div>
      </div>
    </div>
  );
}