import React, { useState } from 'react';
import axios from 'axios';
import Graph from './components/Graph';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [response, setResponse] = useState('');
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });

  const handleSubmit = async () => {
    const res = await axios.post('http://localhost:5000/chat', { input });
    setResponse(res.data.response);
    setGraphData(res.data.graphData);
  };

  return (
    <div className="App">
      <h1>Chatbot with Knowledge Graph</h1>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type your question..."
      />
      <button onClick={handleSubmit}>Send</button>
      <div className="response">{response}</div>
      <Graph data={graphData} />
    </div>
  );
}

export default App;
