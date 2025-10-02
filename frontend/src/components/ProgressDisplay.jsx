import React from 'react';

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

export default ProgressDisplay;