import React from 'react';

const JobDescriptionDisplay = ({ jobData, onTryAnother }) => {
  if (!jobData) return null;

  return (
    <div
      style={{
        width: '100%',
        maxWidth: '56rem',
        color: 'white',
        padding: '0',
        marginTop: '0',
        backgroundColor: 'transparent', // transparent background
      }}
    >
      {/* Job Description */}
      <div
        style={{
          overflowY: 'auto', // scroll if really long
          fontSize: '0.875rem',
          lineHeight: '1.5',
          color: 'white',
          backgroundColor: 'transparent',
          padding: '0',
          borderRadius: '0',
          whiteSpace: 'pre-wrap',
          fontFamily: 'monospace',
          border: 'none',
          marginTop: '1rem',
          scrollbarWidth: 'none', // Firefox
          msOverflowStyle: 'none', // IE/Edge
        }}
      >
        {/* Hide scrollbar for WebKit browsers (Chrome, Safari) */}
        <style>
          {`
            div::-webkit-scrollbar {
              display: none;
            }
          `}
        </style>

        {/* Render backend HTML as-is */}
        {jobData}
      </div>
    </div>
  );
};

export default JobDescriptionDisplay;
