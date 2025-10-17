import React, { useState, memo, useRef, useEffect, forwardRef, useImperativeHandle } from "react";

const Bulk_Input_Form = memo(forwardRef(({
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

Bulk_Input_Form.displayName = 'Bulk_Input_Form';

export default Bulk_Input_Form;
