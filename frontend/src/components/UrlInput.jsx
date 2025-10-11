import React, { useState, memo } from "react";
import JobDescriptionDisplay from "./JobDescriptionDisplay";

const UrlInput = ({ onSubmissionChange, isSubmitted }) => {
  const [url, setUrl] = useState('');
  const [progressMessages, setProgressMessages] = useState([]);
  const [jobData, setJobData] = useState(null);
  const [showParseModal, setShowParseModal] = useState(false);
  const [parseMode, setParseMode] = useState('DOM Parse');

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
            console.error(progressText.scrapingError, data.message);
            setProgressMessages(prev => [...prev, `${progressText.scrapingError} ${data.message}`]);
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

  // UrlInputForm component (memoized)
  const UrlInputForm = memo(({ url, onUrlChange, onSubmit, isBottom = false, showParseModal, setShowParseModal, parseMode }) => {
    const inputStyle = {
      flex: 1,
      padding: '0.75rem 0.5rem',
      fontSize: '1rem',
      border: 'none',
      outline: 'none',
      background: 'transparent'
    };

    const parseButtonStyle = {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '2rem',
      height: '2rem',
      borderRadius: '0.5rem',
      border: '0.5px solid #e5e7eb',
      backgroundColor: 'transparent',
      color: '#9ca3af',
      cursor: 'pointer',
      transition: 'all 0.2s',
      marginLeft: '0.25rem',
      flexShrink: 0
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
      <div style={{ position: 'relative', width: '100%' }}>
  <form onSubmit={onSubmit} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'white', padding: '0.35rem 0.5rem', borderRadius: '0.5rem', boxShadow: '0 1px 2px rgba(16,24,40,0.04)', border: '1px solid #e6e6e6' }}>
          {/* Left plus button (open popover) */}
          <button
            type="button"
            onClick={() => setShowParseModal(!showParseModal)}
            style={{
              width: '2.25rem',
              height: '2.25rem',
              borderRadius: '0.5rem',
              border: 'none',
              background: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '0.5rem',
              cursor: 'pointer'
            }}
            aria-label="Open tools"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 5v14M5 12h14" stroke="#111827" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          <input
            type="text"
            value={url}
            onChange={(e) => onUrlChange(e.target.value)}
            placeholder="LinkedIn, Indeed, Glassdoor URL..."
            style={inputStyle}
          />

          {/* only show submit in the bottom (fixed) input */}
          {isBottom && (
            <button type="submit" style={buttonStyle}>
              {isBottom ? '→' : 'Generate Resume'}
            </button>
          )}
        </form>

        {/* Popover content anchored to the left button */}
        {showParseModal && (
          <div style={{ position: 'absolute', top: '-0.5rem', left: '0.5rem', zIndex: 1500, transform: 'translateY(-100%)' }}>
            <div style={{ width: '220px', background: 'white', borderRadius: '0.75rem', boxShadow: '0 12px 30px rgba(2,6,23,0.08)', padding: '0.5rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {/* menu items matching screenshot */}
                <button onClick={() => { setParseMode('Add photos & files'); setShowParseModal(false); }} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.6rem 0.75rem', border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M21 15V9a3 3 0 0 0-3-3H6" stroke="#111827" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  <span style={{ color: '#111827' }}>Add photos & files</span>
                </button>

                <button onClick={() => { setParseMode('Deep research'); setShowParseModal(false); }} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.6rem 0.75rem', border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M21 21l-4.35-4.35" stroke="#111827" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><circle cx="11" cy="11" r="6" stroke="#111827" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  <span style={{ color: '#111827' }}>Deep research</span>
                </button>

                <button onClick={() => { setParseMode('Create image'); setShowParseModal(false); }} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.6rem 0.75rem', border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="2" stroke="#111827" strokeWidth="1.5"/><circle cx="8.5" cy="8.5" r="1.5" fill="#111827"/></svg>
                  <span style={{ color: '#111827' }}>Create image</span>
                </button>

                <button onClick={() => { setParseMode('Agent mode'); setShowParseModal(false); }} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.6rem 0.75rem', border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 2v4" stroke="#111827" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M7 7h10v10a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V7z" stroke="#111827" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  <span style={{ color: '#111827' }}>Agent mode</span>
                </button>

                <button onClick={() => { setParseMode('Add sources'); setShowParseModal(false); }} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.6rem 0.75rem', border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M10 13a5 5 0 0 0 7.07 0l1.42-1.42" stroke="#111827" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M14 11a5 5 0 0 0-7.07 0L5.51 12.42" stroke="#111827" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  <span style={{ color: '#111827' }}>Add sources</span>
                </button>

                <div style={{ height: '8px', borderTop: '1px solid #f3f4f6', margin: '6px 0' }} />

                <button onClick={() => setShowParseModal(false)} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.6rem 0.75rem', border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left', color: '#6b7280' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M9 18l6-6-6-6" stroke="#6b7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  <span>More</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  });

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
            {/* Outer chat container: input on left, Generate Resume on right */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ flex: 1 }}>
                <UrlInputForm url={url} onUrlChange={setUrl} onSubmit={onSubmit} showParseModal={showParseModal} setShowParseModal={setShowParseModal} parseMode={parseMode} />
              </div>

              <div style={{ flexShrink: 0 }}>
                <button
                  type="button"
                  onClick={() => onSubmit({ preventDefault: () => {} })}
                  style={{
                    background: 'linear-gradient(90deg, #7c3aed, #6d28d9, #5b21b6)',
                    backgroundSize: '200% 200%',
                    animation: 'gradientAnimation 3s ease infinite',
                    color: 'white',
                    fontWeight: '500',
                    height: '2.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '0 1rem',
                    borderRadius: '0.5rem',
                    border: 'none',
                    fontSize: '1rem',
                    cursor: 'pointer'
                  }}
                >
                  Generate Resume
                </button>
              </div>
            </div>
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

      {/* Parse Mode Popover (anchored to input) - rendered inside the UrlInputForm */}

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
        borderRadius: '0.5rem',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        padding: '1.5rem',
        bottom: '20px',
        transition: 'all 0.5s',
        display: isSubmitted ? 'block' : 'none'
      }}>
        <UrlInputForm url={url} onUrlChange={setUrl} onSubmit={handleSubmit} isBottom={true} showParseModal={showParseModal} setShowParseModal={setShowParseModal} parseMode={parseMode} />
      </div>
    </div>
  );
};

export default UrlInput;
