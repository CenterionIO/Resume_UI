import React from 'react';

const JobDescriptionDisplay = ({ jobData, onTryAnother }) => {
  if (!jobData) return null;

  return (
    <div style={{
      width: '100%',
      maxWidth: '56rem',
      color: 'white',
      padding: '0',
      marginTop: '0'
    }}>
      {/* Job Description in white text */}
      <div style={{
        maxHeight: '400px',
        overflowY: 'auto',
        fontSize: '0.875rem',
        lineHeight: '1.5',
        color: 'white',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        whiteSpace: 'pre-wrap',
        fontFamily: 'monospace',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        marginTop: '1rem'
      }}>
        {jobData}
      </div>
      
      {/* Action buttons */}
      <div style={{
        marginTop: '1.5rem',
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
            color: 'white',
            fontWeight: '500',
            padding: '0.75rem 1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid rgba(255, 255, 255, 0.3)',
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

export default JobDescriptionDisplay;