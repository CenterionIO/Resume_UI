import { useState } from 'react';

const UrlInput = ({ onSubmissionChange, isSubmitted }) => {
  const [url, setUrl] = useState('');
  const [progressIndex, setProgressIndex] = useState(0);
  const [jobData, setJobData] = useState(null);

  // Handler for "Try Another Job" button
  const handleTryAnother = () => {
    setUrl('');
    setProgressIndex(0);
    setJobData(null);
    onSubmissionChange(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url) return;

    console.log('Submitting URL:', url);
    onSubmissionChange(true);
    setJobData(null);
    setProgressIndex(0);

    try {
      console.log('Testing backend connection...');

      const ws = new WebSocket('ws://localhost:8000/ws/scrape-progress');

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        ws.send(JSON.stringify({ url: url }));
      };

      ws.onmessage = (event) => {
        console.log('📨 WebSocket message:', event.data);
        try {
          const data = JSON.parse(event.data);

          if (data.message) {
            console.log('Progress message:', data.message);
            if (data.message.includes("Checking LinkedIn session") || data.message.includes("Attempt")) setProgressIndex(0);
            else if (data.message.includes("signing in") || data.message.includes("Logging")) setProgressIndex(1);
            else if (data.message.includes("Login successful")) setProgressIndex(2);
            else if (data.message.includes("Navigating to Job Posting") || data.message.includes("job URL")) setProgressIndex(3);
            else if (data.message.includes("Extracting") || data.message.includes("Fetching")) setProgressIndex(4);
            else if (data.message.includes("Extraction complete") || data.message.includes("Readying")) setProgressIndex(5);
          }

          if (data.type === 'complete') {
            console.log('✅ Scraping completed');
            setJobData(data.job_data || "Job description content would appear here");
            setProgressIndex(6);
            ws.close();
          }

          if (data.type === 'error') {
            console.error('❌ Scraping error:', data.error);
            setProgressIndex(-1);
            ws.close();
          }
        } catch (parseError) {
          console.error('Error parsing WebSocket message:', parseError);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket connection error:', error);
        setProgressIndex(-1);
        // Fallback with mock data
        setJobData(`WebSocket connection failed. Using mock data for: ${url}\n\n🏢 **Company:** Example Corp\n📝 **Title:** Senior Developer\n📍 **Location:** Remote\n💰 **Salary:** $120,000 - $160,000\n\nThis is mock data because the backend connection failed.`);
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
      };

    } catch (error) {
      console.error('❌ Error setting up WebSocket:', error);
      setProgressIndex(-1);
      setJobData(`Error: ${error.message}\n\nUsing fallback mock data for: ${url}`);
    }
  };

  // ProgressDisplay component
  const ProgressDisplay = ({ progressIndex, jobData }) => {
    const messages = [
      "Navigating to URL...",
      "Logging into LinkedIn...", 
      "Login success...",
      "Navigating to Job Posting...",
      "Fetching job description...",
      "Readying job description"
    ];

    return (
      <div style={{
        width: '100%',
        maxWidth: '48rem',
        flex: 1,
        overflowY: 'auto',
        marginBottom: '1rem',
        textAlign: 'center'
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
          {progressIndex === -1 ? (
            "❌ Error scraping job. Please try again."
          ) : progressIndex === 6 ? (
            jobData ? "✅ Job description ready!" : "Processing..."
          ) : (
            messages[progressIndex] || "Starting..."
          )}
        </div>
      </div>
    );
  };

  // JobDescriptionDisplay component
  const JobDescriptionDisplay = ({ jobData, onTryAnother }) => {
    if (!jobData) return null;

    return (
      <div style={{
        width: '100%',
        maxWidth: '56rem',
        backgroundColor: 'white',
        borderRadius: '0.75rem',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        padding: '2rem',
        marginTop: '2rem'
      }}>
        <h3 style={{
          fontSize: '1.5rem',
          fontWeight: '600',
          color: '#1f2937',
          marginBottom: '1rem',
          borderBottom: '2px solid #e5e7eb',
          paddingBottom: '0.5rem'
        }}>
          📋 Job Description
        </h3>
        <div style={{
          maxHeight: '400px',
          overflowY: 'auto',
          fontSize: '0.875rem',
          lineHeight: '1.5',
          color: '#374151',
          backgroundColor: '#f9fafb',
          padding: '1rem',
          borderRadius: '0.5rem',
          whiteSpace: 'pre-wrap',
          fontFamily: 'monospace'
        }}>
          {jobData}
        </div>
        <div style={{
          marginTop: '1rem',
          display: 'flex',
          gap: '1rem'
        }}>
          <button style={{
            background: 'linear-gradient(90deg, #10b981, #059669, #047857)',
            backgroundSize: '200% 200%',
            animation: 'gradientAnimation 3s ease infinite',
            color: 'white',
            fontWeight: '500',
            padding: '0.75rem 1.5rem',
            borderRadius: '0.5rem',
            border: 'none',
            cursor: 'pointer',
            fontSize: '0.875rem'
          }}>
            Generate Resume from this Job
          </button>
          
          <button 
            onClick={onTryAnother}
            style={{
              background: 'transparent',
              color: '#6b7280',
              fontWeight: '500',
              padding: '0.75rem 1.5rem',
              borderRadius: '0.5rem',
              border: '1px solid #d1d5db',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            Try Another Job
          </button>
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
        alignItems: 'center',
        justifyContent: 'flex-start',
        padding: '1.5rem 1rem 3rem 1rem'
      }}>
        <InitialContent url={url} onUrlChange={setUrl} onSubmit={handleSubmit} isVisible={!isSubmitted} />

        {isSubmitted && <ProgressDisplay progressIndex={progressIndex} jobData={jobData} />}

        <JobDescriptionDisplay jobData={jobData} onTryAnother={handleTryAnother} />
      </main>

      {/* Bottom Input */}
      <div style={{
        position: 'fixed',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '90%',
        maxWidth: '56rem',
        backgroundColor: 'white',
        borderRadius: '0.75rem',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        border: '1px solid #e5e7eb',
        padding: '1.5rem',
        bottom: '20px',
        transition: 'all 0.5s',
        display: isSubmitted ? 'block' : 'none'
      }}>
        <UrlInputForm 
          url={url}
          onUrlChange={setUrl}
          onSubmit={handleSubmit}
          isBottom={true}
        />
      </div>
    </div>
  );
};

export default UrlInput;