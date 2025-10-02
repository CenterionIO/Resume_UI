// frontend/src/hooks/useWebSocket.js
import { useState, useEffect, useRef, useCallback } from 'react';

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const websocket = useRef(null);

  // Use useCallback to prevent unnecessary re-renders
  const connect = useCallback((url, onMessage, onError, onClose) => {
    try {
      setError(null);
      const sessionId = localStorage.getItem('linkedin_session_id');
      websocket.current = new WebSocket('ws://localhost:8000/ws/scrape-progress');
      
      websocket.current.onopen = () => {
        setIsConnected(true);
        console.log('🔗 WebSocket connected');
        
        const message = {
          url: url,
          session_id: sessionId
        };
        websocket.current.send(JSON.stringify(message));
      };

      websocket.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message:', data);
          
          // Handle session persistence
          if (data.type === 'new_session' || data.type === 'session_found') {
            localStorage.setItem('linkedin_session_id', data.session_id);
            console.log('💾 Session ID stored:', data.session_id);
          }
          
          if (onMessage) onMessage(data);
        } catch (parseError) {
          console.error('❌ Failed to parse WebSocket message:', parseError);
        }
      };

      websocket.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setError(error);
        if (onError) onError(error);
      };

      websocket.current.onclose = (event) => {
        setIsConnected(false);
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        if (onClose) onClose(event);
      };
    } catch (error) {
      console.error('❌ WebSocket connection failed:', error);
      setError(error);
      if (onError) onError(error);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (websocket.current) {
      websocket.current.close(1000, 'User initiated disconnect');
      websocket.current = null;
    }
  }, []);

  // Auto-cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    isConnected,
    error
  };
};