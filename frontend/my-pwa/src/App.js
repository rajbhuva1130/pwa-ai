// ⬆️ imports always first
import React, { useState } from "react";
import axios from "axios";
import "./App.css"; // optional if you have styling

function App() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello! How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { role: "user", content: input }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post(
        "http://localhost:8000/chat",
        new URLSearchParams({ prompt: input }),
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );

      setMessages([...newMessages, { role: "assistant", content: res.data.response }]);
    } catch (err) {
      setMessages([...newMessages, { role: "assistant", content: "⚠️ Error connecting to backend." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-black text-white">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg max-w-xl ${
              msg.role === "user" ? "bg-blue-600 self-end" : "bg-gray-700 self-start"
            }`}
          >
            {msg.content}
          </div>
        ))}
        {loading && <div className="italic text-gray-400">Assistant is typing...</div>}
      </div>

      <div className="p-4 border-t border-gray-700 flex">
        <input
          className="flex-1 p-3 rounded-lg bg-gray-800 text-white focus:outline-none"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          className="ml-2 px-4 py-2 bg-blue-600 rounded-lg"
          onClick={sendMessage}
          disabled={loading}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default App;
// ⬇️ exports always last