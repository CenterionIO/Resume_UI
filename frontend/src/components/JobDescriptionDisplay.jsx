import React from 'react';

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

export default JobDescriptionDisplay;