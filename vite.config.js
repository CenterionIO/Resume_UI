// Temporary polling hook (src/hooks/usePolling.js)
import { useState, useEffect } from 'react';

export const usePolling = (sessionId) => {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!sessionId) return;

    setIsConnected(true);
    
    // Simulate progress with polling
    const steps = [
      "Starting process...",
      "Analyzing requirements...", 
      "Generating content...",
      "Complete!"
    ];
    
    let step = 0;
    const interval = setInterval(() => {
      if (step < steps.length) {
        setMessages(prev => [...prev, {
          message: steps[step],
          timestamp: new Date().toISOString(),
          id: Date.now()
        }]);
        step++;
      } else {
        clearInterval(interval);
        setIsConnected(false);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [sessionId]);

  return { messages, isConnected };
};