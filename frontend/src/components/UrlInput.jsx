import React, { useState, memo, useRef, useEffect, forwardRef, useImperativeHandle } from "react";
import { createPortal } from 'react-dom';
import JobDescriptionDisplay from "./JobDescriptionDisplay";

// Move BulkInputForm to module scope so it isn't re-declared on every UrlInput render.
const BulkInputForm = memo(forwardRef(({
  showParseModal,
  setShowParseModal,
  setActivePopoverAnchor,
  activePopoverAnchor,
  onBulkSubmit
}, ref) => {
  const toolsButtonRef = useRef(null);

  const [localKeyword, setLocalKeyword] = useState('');
  const [localLocation, setLocalLocation] = useState('');
  const [localPages, setLocalPages] = useState(1);

  const bulkKeywordRef = useRef(null);
  const bulkLocationRef = useRef(null);

  useEffect(() => {
    console.log('[BulkInputForm] mounted');
    return () => console.log('[BulkInputForm] unmounted');
  }, []);

  useImperativeHandle(ref, () => ({
    submit: () => {
      if (typeof onBulkSubmit === 'function') {
        onBulkSubmit(localKeyword, localLocation, localPages);
      }
    }
  }), [localKeyword, localLocation, localPages, onBulkSubmit]);

  return (
    <div style={{ position: 'relative', background: 'white', padding: '1rem', borderRadius: '0.5rem', boxShadow: '0 1px 2px rgba(16,24,40,0.04)', border: '1px solid #e6e6e6' }}>
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.75rem' }}>
        <button
          ref={toolsButtonRef}
          type="button"
          onClick={() => {
            if (!showParseModal || activePopoverAnchor !== 'bulk') {
              setActivePopoverAnchor('bulk');
              setShowParseModal(true);
            } else {
              setShowParseModal(false);
              setActivePopoverAnchor(null);
            }
          }}
          style={{
            width: '2.25rem',
            height: '2.25rem',
            borderRadius: '0.5rem',
            border: 'none',
            background: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            flexShrink: 0
          }}
          aria-label="Open tools"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5v14M5 12h14" stroke="#111827" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <input
          type="text"
          value={localKeyword}
          onChange={(e) => setLocalKeyword(e.target.value)}
          placeholder="Job title (e.g., AI Engineer)"
          ref={bulkKeywordRef}
          style={{
            flex: 1,
            padding: '0.5rem',
            fontSize: '1rem',
            border: '1px solid #e5e7eb',
            borderRadius: '0.375rem',
            outline: 'none'
          }}
        />
        <input
          type="text"
          value={localLocation}
          onChange={(e) => setLocalLocation(e.target.value)}
          placeholder="Location (e.g., United States)"
          ref={bulkLocationRef}
          style={{
            flex: 1,
            padding: '0.5rem',
            fontSize: '1rem',
            border: '1px solid #e5e7eb',
            borderRadius: '0.375rem',
            outline: 'none'
          }}
        />
      </div>
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', paddingLeft: '2.75rem' }}>
        <label style={{ fontSize: '0.875rem', color: '#6b7280' }}>Pages:</label>
        <select
          value={localPages}
          onChange={(e) => setLocalPages(parseInt(e.target.value))}
          style={{
            padding: '0.5rem',
            fontSize: '0.875rem',
            border: '1px solid #e5e7eb',
            borderRadius: '0.375rem',
            outline: 'none',
            background: 'white'
          }}
        >
          {[1, 2, 3, 4, 5].map(num => (
            <option key={num} value={num}>{num}</option>
          ))}
        </select>
        <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
          (~{localPages * 10} jobs)
        </span>
      </div>
    </div>
  );
}));

const UrlInput = ({ onSubmissionChange, isSubmitted }) => {
  const [url, setUrl] = useState('');
  const [progressMessages, setProgressMessages] = useState([]);
  const [jobData, setJobData] = useState(null);
  const [showParseModal, setShowParseModal] = useState(false);
  const [parseMode, setParseMode] = useState('DOM Parse');
  const [activePopoverAnchor, setActivePopoverAnchor] = useState(null);

  // Bulk scrape state
  const [bulkKeyword, setBulkKeyword] = useState('');
  const [bulkLocation, setBulkLocation] = useState('');
  const [bulkPages, setBulkPages] = useState(1);
  const [bulkJobs, setBulkJobs] = useState([]);
  const bulkInputRef = useRef(null);

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
    setBulkJobs([]);
    onSubmissionChange(false);
  };

  // Bulk submit that accepts parameters (used by BulkInputForm via ref)
  const handleBulkSubmit = (keyword, location, pages) => {
    if (!keyword || !location) return;

    console.log('Submitting bulk scrape:', keyword, location, pages);
    onSubmissionChange(true);
    setJobData(null);
    setBulkJobs([]);
    setProgressMessages([]);

    try {
      console.log('Connecting to bulk scrape WebSocket...');

      const ws = new WebSocket('ws://localhost:8000/ws/bulk-scrape');

      ws.onopen = () => {
        console.log('✅ Bulk scrape WebSocket connected');
        ws.send(JSON.stringify({
          keyword,
          location,
          pages
        }));
      };

      ws.onmessage = (event) => {
        console.log('📨 Bulk scrape message:', event.data);
        try {
          const data = JSON.parse(event.data);

          if (data.message) {
            console.log('Progress message:', data.message);
            setProgressMessages(prev => [...prev, data.message]);
          }

          if (data.status === 'job') {
            console.log('Job found:', data.data.title);
            setBulkJobs(prev => [...prev, data.data]);
          }

          if (data.status === 'complete') {
            console.log('✅ Bulk scraping complete');
            setProgressMessages(prev => [...prev, data.message]);
            ws.close();
          }

          if (data.status === 'error') {
            console.error('❌ Bulk scrape error:', data.message);
            setProgressMessages(prev => [...prev, `❌ Error: ${data.message}`]);
            ws.close();
          }

        } catch (parseError) {
          console.error('Error parsing bulk scrape message:', parseError);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ Bulk scrape WebSocket error:', error);
        setProgressMessages(prev => [...prev, '❌ WebSocket connection failed']);
      };

      ws.onclose = (event) => {
        console.log('Bulk scrape WebSocket closed:', event.code, event.reason);
      };

    } catch (error) {
      console.error('❌ Error setting up bulk scrape WebSocket:', error);
      setProgressMessages(prev => [...prev, `❌ Error: ${error.message}`]);
    }
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
  const UrlInputForm = memo(({ instanceId = 'top', url, onUrlChange, onSubmit, isBottom = false, showParseModal, setShowParseModal, parseMode }) => {
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

  const toolsButtonRef = useRef(null);
    const [popoverStyle, setPopoverStyle] = useState({ top: 0, left: 0, visibility: 'hidden' });

    useEffect(() => {
      if (!showParseModal) return;

      const updatePosition = () => {
        const btn = toolsButtonRef.current;
        if (!btn) return;
        const rect = btn.getBoundingClientRect();
        const popoverWidth = 220;
        const margin = 8;
        let left = rect.left + window.scrollX;
        // prefer left aligned to button, but ensure within viewport
        if (left + popoverWidth + margin > window.innerWidth) {
          left = window.innerWidth - popoverWidth - margin;
        }
        if (left < margin) left = margin;

        // position above the button if there's space, otherwise below
        let top = rect.top + window.scrollY - 8; // prefer above
        const popoverHeight = 260; // approximate
        if (top - popoverHeight < 0) {
          // not enough space above, place below
          top = rect.bottom + window.scrollY + 8;
        } else {
          // move up so popover sits above button
          top = rect.top + window.scrollY - popoverHeight - 8 + rect.height;
        }

        setPopoverStyle({ top, left, visibility: 'visible' });
      };

      updatePosition();
      window.addEventListener('resize', updatePosition);
      window.addEventListener('scroll', updatePosition, true);
      return () => {
        window.removeEventListener('resize', updatePosition);
        window.removeEventListener('scroll', updatePosition, true);
      };
    }, [showParseModal, activePopoverAnchor]);

    return (
      <div style={{ position: 'relative', width: '100%' }}>
  <form onSubmit={onSubmit} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'white', padding: '0.35rem 0.5rem', borderRadius: '0.5rem', boxShadow: '0 1px 2px rgba(16,24,40,0.04)', border: '1px solid #e6e6e6' }}>
          {/* Left plus button (open popover) */}
          <button
            ref={toolsButtonRef}
            type="button"
            onClick={() => {
              // toggle this instance as the active anchor
              if (!showParseModal || activePopoverAnchor !== instanceId) {
                setActivePopoverAnchor(instanceId);
                setShowParseModal(true);
              } else {
                setShowParseModal(false);
                setActivePopoverAnchor(null);
              }
            }}
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

  {/* Popover content rendered into body via portal to avoid clipping */}
  {showParseModal && activePopoverAnchor === instanceId && typeof document !== 'undefined' && createPortal(
          <div style={{ position: 'absolute', top: popoverStyle.top + 'px', left: popoverStyle.left + 'px', zIndex: 9999 }}>
            <div style={{ width: '220px', background: 'white', borderRadius: '0.75rem', boxShadow: '0 12px 30px rgba(2,6,23,0.08)', padding: '0.5rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                <button onClick={() => { setParseMode('DOM Parse'); setShowParseModal(false); setActivePopoverAnchor(null); }} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.6rem 0.75rem', border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left' }}>
                  <span style={{ width: '1rem', textAlign: 'center' }}>🔎</span>
                  <span style={{ color: '#111827' }}>DOM Parse</span>
                </button>
                <button onClick={() => { setParseMode('Bulk Parse'); setShowParseModal(false); setActivePopoverAnchor(null); }} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.6rem 0.75rem', border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left' }}>
                  <span style={{ width: '1rem', textAlign: 'center' }}>📄</span>
                  <span style={{ color: '#111827' }}>Bulk Parse</span>
                </button>
                <button onClick={() => { setParseMode('Site Parse'); setShowParseModal(false); setActivePopoverAnchor(null); }} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', padding: '0.6rem 0.75rem', border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left' }}>
                  <span style={{ width: '1rem', textAlign: 'center' }}>🌐</span>
                  <span style={{ color: '#111827' }}>Site Parse</span>
                </button>
              </div>
            </div>
          </div>, document.body
        )}
      </div>
    );
  });

  // InitialContent component
  const InitialContent = ({ url, onUrlChange, onSubmit, isVisible }) => {
    if (!isVisible) return null;

    // Determine which submit handler to use
    const handleFormSubmit = parseMode === 'Bulk Parse' ? handleBulkSubmit : onSubmit;

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
                {parseMode === 'Bulk Parse' ? (
                  <BulkInputForm
                    ref={bulkInputRef}
                    onBulkSubmit={handleBulkSubmit}
                    showParseModal={showParseModal}
                    setShowParseModal={setShowParseModal}
                    activePopoverAnchor={activePopoverAnchor}
                    setActivePopoverAnchor={setActivePopoverAnchor}
                  />
                ) : (
                  <UrlInputForm instanceId={'top'} url={url} onUrlChange={setUrl} onSubmit={onSubmit} showParseModal={showParseModal} setShowParseModal={setShowParseModal} parseMode={parseMode} />
                )}
              </div>

              <div style={{ flexShrink: 0 }}>
                <button
                  type="button"
                  onClick={() => {
                    // If bulk mode, trigger the child's submit via ref
                    if (parseMode === 'Bulk Parse' && bulkInputRef.current && typeof bulkInputRef.current.submit === 'function') {
                      bulkInputRef.current.submit();
                    } else {
                      handleFormSubmit({ preventDefault: () => {} });
                    }
                  }}
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

        {/* Bulk Jobs Display - Full descriptions in white text */}
        {bulkJobs.length > 0 && (
          <div style={{ width: '100%', maxWidth: '56rem', marginTop: '1rem' }}>
            <div style={{
              color: 'white',
              backgroundColor: 'transparent',
              fontSize: '1.125rem',
              lineHeight: '1.75',
              fontFamily: 'system-ui, -apple-system, sans-serif'
            }}>
              {bulkJobs.map((job, index) => {
                // Format job description similar to single URL scraping
                const hasDescription = job.description && job.description.trim().length > 0;

                // Show all jobs, even without descriptions (for debugging)
                const metadata = [
                  job.location,
                  job.posted_date_text,
                  job.applicants_detail || job.applicants
                ].filter(Boolean).join(' · ');

                const tags = [
                  job.salary,
                  job.work_type,
                  job.employment_type
                ].filter(Boolean).join(' · ');

                return (
                  <div key={index} style={{ marginBottom: '3rem' }}>
                    {/* Job header */}
                    <div style={{ fontWeight: 700, fontSize: '1.25rem', marginBottom: '0.5rem' }}>
                      {job.company || 'Unknown Company'}
                    </div>

                    <div style={{ fontWeight: 700, fontSize: '1.125rem', marginBottom: '0.75rem' }}>
                      {job.title || 'Untitled Position'}
                    </div>

                    {metadata && (
                      <div style={{ fontSize: '1rem', marginBottom: '0.5rem', opacity: 0.9 }}>
                        {metadata}
                      </div>
                    )}

                    {tags && (
                      <div style={{ fontSize: '1rem', marginBottom: '1rem', opacity: 0.9 }}>
                        {tags}
                      </div>
                    )}

                    {/* Job description */}
                    {hasDescription ? (
                      <div style={{ marginTop: '1rem' }}>
                        <div style={{ fontWeight: 700, marginTop: '1rem', marginBottom: '0.5rem' }}>
                          About the job
                        </div>
                        <div style={{ whiteSpace: 'pre-wrap' }}>
                          {job.description}
                        </div>
                      </div>
                    ) : (
                      <div style={{ marginTop: '1rem', opacity: 0.6, fontStyle: 'italic' }}>
                        [Description not available - check backend logs for details]
                      </div>
                    )}

                    {/* Separator line between jobs */}
                    {index < bulkJobs.length - 1 && (
                      <div style={{
                        borderTop: '1px solid rgba(255, 255, 255, 0.2)',
                        marginTop: '2rem'
                      }} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
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
  <UrlInputForm instanceId={'bottom'} url={url} onUrlChange={setUrl} onSubmit={handleSubmit} isBottom={true} showParseModal={showParseModal} setShowParseModal={setShowParseModal} parseMode={parseMode} />
      </div>
    </div>
  );
};

export default UrlInput;
