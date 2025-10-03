import React from 'react';

const JobDescriptionDisplay = ({ jobData, onTryAnother }) => {
  if (!jobData) return null;

  return (
    <div style={{
      width: '100%',
      maxWidth: '56rem',
      color: 'white',
      padding: '0',
      marginTop: '0',
      backgroundColor: 'transparent', // Ensure no background
    }}>
      {/* Job Description - Clean styling without borders or scrollbar */}
      <div style={{
        maxHeight: '400px',
        overflowY: 'auto', // Keep scroll functionality but we'll hide the scrollbar
        fontSize: '0.875rem',
        lineHeight: '1.5',
        color: 'white',
        backgroundColor: 'transparent', // Remove the semi-transparent background
        padding: '0', // Remove padding
        borderRadius: '0', // Remove border radius
        whiteSpace: 'pre-wrap',
        fontFamily: 'monospace',
        border: 'none', // Remove border
        marginTop: '1rem',
        // Hide scrollbar but keep functionality
        scrollbarWidth: 'none', // Firefox
        msOverflowStyle: 'none', // IE/Edge
      }}>
        {/* Hide scrollbar for Webkit browsers (Chrome, Safari) */}
        <style>
          {`
            div::-webkit-scrollbar {
              display: none;
            }
          `}
        </style>
        {jobData}
      </div>
      
      {/* Buttons removed as requested */}
    </div>
  );
};

export default JobDescriptionDisplay;