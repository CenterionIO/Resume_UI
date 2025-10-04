import React, { useState } from "react";
import JobDescriptionDisplay from "./JobDescriptionDisplay";

const UrlInput = ({ onSubmissionChange, isSubmitted }) => {
  const [url, setUrl] = useState('');
  const [progressMessages, setProgressMessages] = useState([]);
  const [jobData, setJobData] = useState(null);

  // Progress update text configuration
  const progressText = {
    wsConnecting: 'Testing backend connection...',
    wsConnected: '✅ WebSocket connected',
    wsConnectionFailed: '❌ WebSocket connection failed',
    wsError: '❌ Error setting up WebSocket:',
    scrapingComplete: '✅ Scraping completed!',
    scrapingError: '❌ Scraping error:',
    newSession: '🔐 New session created',
    sessionFound: '🔐 Existing session found',
    starting: 'Starting...',
    connectionFailed: 'Connection failed',
    mockDataFallback: (url) => `WebSocket connection failed. Using mock data for: ${url}\n\n🏢 **Company:** Example Corp\n📝 **Title:** Senior Developer\n📍 **Location:** Remote\n💰 **Salary:** $120,000 - $160,000\n\nThis is mock data because the backend connection failed.`,
    errorFallback: (error, url) => `Error: ${error}\n\nUsing fallback mock data for: ${url}`
  };

  // Handler for "Try Another Job" button
  const handleTryAnother = () => {
    setUrl('');
    setProgressMessages([]);
    setJobData(null);
    onSubmissionChange(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url) return;

    console.log('Submitting URL:', url);
    onSubmissionChange(true);
    setJobData(null);
    setProgressMessages([]);

    try {
      console.log(progressText.wsConnecting);

      const ws = new WebSocket('ws://localhost:8000/ws/scrape-progress');

      ws.onopen = () => {
        console.log(progressText.wsConnected);
        ws.send(JSON.stringify({ url: url }));
      };

      ws.onmessage = (event) => {
        console.log('📨 WebSocket message:', event.data);
        try {
          const data = JSON.parse(event.data);

          if (data.message) {
            console.log('Progress message:', data.message);
            setProgressMessages(prev => [...prev, data.message]);
          }

          if (data.type === 'complete') {
            console.log(progressText.scrapingComplete);

            // ✅ Use backend’s parsed HTML directly
            setJobData(data.job_data || "Job description content would appear here");

            setProgressMessages(prev => [...prev, progressText.scrapingComplete]);
            ws.close();
          }

          if (data.type === 'error') {
            console.error(progressText.scrapingError, data.error);
            setProgressMessages(prev => [...prev, `${progressText.scrapingError} ${data.error}`]);
            ws.close();
          }

          if (data.type === 'new_session') {
            console.log('Session update:', data.message);
            setProgressMessages(prev => [...prev, `${progressText.newSession}: ${data.message}`]);
          }

          if (data.type === 'session_found') {
            console.log('Session update:', data.message);
            setProgressMessages(prev => [...prev, `${progressText.sessionFound}: ${data.message}`]);
          }

        } catch (parseError) {
          console.error('Error parsing WebSocket message:', parseError);
        }
      };

      ws.onerror = (error) => {
        console.error(progressText.wsConnectionFailed, error);
        setProgressMessages(prev => [...prev, progressText.wsConnectionFailed]);
        setJobData(progressText.mockDataFallback(url));
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
      };

    } catch (error) {
      console.error(progressText.wsError, error);
      setProgressMessages(prev => [...prev, `${progressText.wsError} ${error.message}`]);
      setJobData(progressText.errorFallback(error.message, url));
    }
  };

  // ProgressDisplay component
  const ProgressDisplay = ({ progressMessages, jobData }) => {
    const currentMessage = progressMessages.length > 0 ? progressMessages[progressMessages.length - 1] : progressText.starting;

    return (
      <div style={{
        width: '100%',
        maxWidth: '48rem',
        flex: 1,
        overflowY: 'auto',
        marginBottom: '1rem',
        textAlign: 'left',
        paddingLeft: '1rem'
      }}>
        <div style={{
          background: 'linear-gradient(90deg, #ffffff, #d1d5db, #ffffff)',
          backgroundSize: '200% 200%',
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          color: 'transparent',
          animation: 'gradientAnimation 3s ease infinite',
          padding: '0.5rem 1rem',
          borderRadius: '0.5rem',
          display: 'inline-block',
          fontSize: '1.125rem',
          fontWeight: '500'
        }}>
          {currentMessage}
        </div>
      </div>
    );
  };

  // UrlInputForm component
  const UrlInputForm = ({ url, onUrlChange, onSubmit, isBottom = false }) => {
    const inputStyle = {
      flex: 1,
      padding: '1rem',
      fontSize: '1.125rem',
      borderRadius: '0.5rem',
      border: '1px solid #d1d5db',
      outline: 'none'
    };

    const buttonStyle = {
      background: 'linear-gradient(90deg, #7c3aed, #6d28d9, #5b21b6)',
      backgroundSize: '200% 200%',
      animation: 'gradientAnimation 3s ease infinite',
      color: 'white',
      fontWeight: '500',
      padding: isBottom ? '1rem 1.5rem' : '1rem 2rem',
      borderRadius: '0.5rem',
      border: 'none',
      fontSize: '1.125rem',
      minWidth: isBottom ? 'auto' : '180px',
      cursor: 'pointer'
    };

    return (
      <form onSubmit={onSubmit} style={{ display: 'flex', gap: '0.75rem' }}>
        <input 
          type="text" 
          value={url}
          onChange={(e) => onUrlChange(e.target.value)}
          placeholder="LinkedIn, Indeed, Glassdoor URL..." 
          style={inputStyle}
        />
        <button type="submit" style={buttonStyle}>
          {isBottom ? '→' : 'Generate Resume'}
        </button>
      </form>
    );
  };

  // InitialContent component
  const InitialContent = ({ url, onUrlChange, onSubmit, isVisible }) => {
    if (!isVisible) return null;

    return (
      <div style={{
        width: '100%',
        maxWidth: '56rem',
        backgroundColor: 'white',
        borderRadius: '0.75rem',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        overflow: 'hidden',
        transition: 'all 1s ease-in-out',
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(-5rem)'
      }}>
        <div style={{ padding: '2rem', width: '100%' }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <UrlInputForm url={url} onUrlChange={onUrlChange} onSubmit={onSubmit} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem', marginLeft: '0.5rem' }}>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', whiteSpace: 'nowrap' }}>Supported job platforms:</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
              {['LinkedIn', 'Indeed', 'Glassdoor', 'AngelList', 'Wellfound'].map((platform) => (
                <span key={platform} style={{ padding: '0.25rem 0.75rem', backgroundColor: '#f3f4f6', borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.875rem' }}>
                  {platform}
                </span>
              ))}
            </div>
          </div>

          <div style={{ backgroundColor: '#f9fafb', padding: '1.5rem', borderRadius: '0.5rem' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '500', marginBottom: '1rem' }}>Features</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', fontSize: '0.875rem' }}>
              {[
                'ATS optimization', 'Keyword matching', 'Bullet enhancement', 'Skills alignment',
                'Format perfecting', 'Industry phrasing', 'Experience matching', 'Education optimization',
                'Certification alignment'
              ].map((feature) => (
                <div key={feature} style={{ display: 'flex', alignItems: 'center' }}>
                  <span style={{ width: '1rem', height: '1rem', marginRight: '0.5rem', color: '#10b981' }}>✓</span>
                  {feature}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      backgroundSize: '200% 200%',
      animation: 'gradientAnimation 15s ease infinite',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <header style={{
        textAlign: 'center',
        paddingTop: '7rem',
        paddingBottom: '1rem',
        paddingLeft: '1rem',
        paddingRight: '1rem',
        transition: 'all 1s ease-in-out',
        opacity: isSubmitted ? 0 : 1,
        transform: isSubmitted ? 'translateY(-5rem)' : 'translateY(0)',
        display: isSubmitted ? 'none' : 'block'
      }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: '700', color: 'white', marginBottom: '0.5rem' }}>
          AI Resume Generator
        </h1>
        <p style={{ fontSize: '1.25rem', color: 'rgba(255, 255, 255, 0.9)' }}>
          Test ATS systems with perfectly tailored resumes
        </p>
      </header>

      {/* Main Content */}
      <main style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        justifyContent: 'flex-start',
        padding: '1.5rem 1rem 3rem 1rem',
        width: '100%',
        maxWidth: '56rem',
        margin: '0 auto'
      }}>
        <InitialContent url={url} onUrlChange={setUrl} onSubmit={handleSubmit} isVisible={!isSubmitted} />

        {/* Progress Display */}
        {isSubmitted && (
          <div style={{ width: '100%', marginBottom: '1rem' }}>
            <ProgressDisplay progressMessages={progressMessages} jobData={jobData} />
          </div>
        )}

        {/* Job Description Display */}
        <JobDescriptionDisplay jobData={jobData} onTryAnother={handleTryAnother} />
      </main>

      {/* Bottom Input */}
      <div style={{
        position: 'fixed',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '90%',
        maxWidth: '56rem',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderRadius: '0.75rem',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        padding: '1.5rem',
        bottom: '20px',
        transition: 'all 0.5s',
        display: isSubmitted ? 'block' : 'none'
      }}>
        <UrlInputForm url={url} onUrlChange={setUrl} onSubmit={handleSubmit} isBottom={true} />
      </div>
    </div>
  );
};

export default UrlInput;
