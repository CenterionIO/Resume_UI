import React from 'react';

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

export default UrlInputForm;