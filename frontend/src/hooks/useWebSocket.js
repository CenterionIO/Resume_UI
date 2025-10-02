import { useState, useEffect, useRef } from 'react';

export const useWebSocket = (sessionId) => {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    if (!sessionId) {
      setIsConnected(false);
      return;
    }

    const connect = () => {
      try {
        // Use the same origin for WebSocket to avoid CORS issues
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host; // This will be localhost:3000 (Vite)
        const wsUrl = `ws://localhost:8000/ws`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
          console.log('WebSocket connected successfully');
          setIsConnected(true);
        };

        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            setMessages(prev => [...prev, {
              ...data,
              id: Date.now() + Math.random(),
              status: data.message === 'complete' ? 'completed' : 'active'
            }]);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.current.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          setIsConnected(false);
          // Don't auto-reconnect for now to avoid spam
        };

        ws.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setIsConnected(false);
        };

      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setIsConnected(false);
      }
    };

    connect();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [sessionId]);

  const sendMessage = (message) => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return { messages, isConnected, sendMessage };
};