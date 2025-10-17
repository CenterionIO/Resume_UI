import React from 'react';

const Frontend_Styling = ({ jobData, onTryAnother }) => {
  if (!jobData) return null;

  // Process the job data to add bold formatting to headers
  const formatJobData = (text) => {
    const lines = text.split('\n');
    const nodes = [];
    const bulletRegex = /^\s*[-\u2022\*–—]\s+/; // -, •, *, –, —

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmedLine = line.trim();

      if (trimmedLine === '') {
        // blank line -> small spacer
        nodes.push(<div key={`b-${i}`} style={{ height: '6px' }} />);
        continue;
      }

      // Header detection (using surrounding lines)
      const prevLine = i > 0 ? lines[i - 1].trim() : '';
      const nextLine = i < lines.length - 1 ? lines[i + 1].trim() : '';

      const isHeader = (() => {
        if (!trimmedLine) return false;
        if (i === 0) return true; // first non-empty line - company/title
        if (/^About the job$/i.test(trimmedLine)) return true;
        if (trimmedLine.length <= 60 && prevLine === '' && nextLine === '') return true;
        if (trimmedLine.endsWith(':') && trimmedLine.length <= 60) return true;
        if (trimmedLine.split(' ').length <= 6 && /^[A-Z0-9]/.test(trimmedLine)) return true;
        return false;
      })();

      if (isHeader) {
        const marginTop = nodes.length === 0 ? '0' : '16px';
        nodes.push(
          <div key={`h-${i}`} style={{ fontWeight: 700, marginTop, marginBottom: '6px' }}>
            {trimmedLine}
          </div>
        );
        continue;
      }

      // Handle lists: group consecutive bullet lines into a single <ul>
      if (bulletRegex.test(line)) {
        const items = [];
        // collect consecutive bullet entries
        let j = i;
        while (j < lines.length && lines[j].trim() !== '') {
          const l = lines[j];
          if (bulletRegex.test(l)) {
            // start of a new bullet; collect following continuation lines that are not bullets
            let content = l.replace(bulletRegex, '').trim();
            let k = j + 1;
            while (k < lines.length && lines[k].trim() !== '' && !bulletRegex.test(lines[k])) {
              content += ' ' + lines[k].trim();
              k += 1;
            }
            items.push(content);
            j = k;
          } else {
            // not a bullet; stop collecting bullets
            break;
          }
        }

        // push a ul with collected items
        nodes.push(
          <ul key={`ul-${i}`} style={{ paddingLeft: '1.25rem', marginTop: '8px', marginBottom: '8px' }}>
            {items.map((it, idx) => (
              <li key={`${i}-${idx}`} style={{ marginBottom: '6px', lineHeight: '1.6' }}>{it}</li>
            ))}
          </ul>
        );

        // advance i to the last processed line
        i = Math.max(i, i + items.length - 1);
        // move i forward to j-1 (outer loop will increment)
        i = j - 1;
        continue;
      }

      // Otherwise, collect a paragraph: group consecutive non-blank, non-bullet lines
      let para = trimmedLine;
      let k = i + 1;
      while (k < lines.length && lines[k].trim() !== '' && !bulletRegex.test(lines[k])) {
        para += ' ' + lines[k].trim();
        k += 1;
      }
      nodes.push(<div key={`p-${i}`} style={{ marginBottom: '6px', lineHeight: '1.6' }}>{para}</div>);
      i = k - 1;
    }

    return nodes;
  };

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
          fontSize: '1.125rem', // Larger font (18px)
          lineHeight: '1.75', // More line height (6pt ~ 8px between lines)
          color: 'white',
          backgroundColor: 'transparent',
          padding: '0',
          borderRadius: '0',
          fontFamily: 'system-ui, -apple-system, sans-serif', // Better readability
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

        {/* Render formatted job data */}
        {formatJobData(jobData)}
      </div>
    </div>
  );
};

export default Frontend_Styling;
