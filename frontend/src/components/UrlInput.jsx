// UrlInput.jsx - CONTROLLER ONLY
const UrlInput = ({ onSubmissionChange, isSubmitted }) => {
  const [url, setUrl] = useState('');
  const [progressIndex, setProgressIndex] = useState(-1);
  const [jobData, setJobData] = useState(null); // Can be string, HTML, or JSON
  const [progressMessages, setProgressMessages] = useState([]);

  // Handle WebSocket messages - JUST UPDATE STATE
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'progress') {
      setProgressIndex(data.progress_index);
    }

    if (data.type === 'complete') {
      setJobData(data.job_data); // Just store whatever backend sends
      setProgressIndex(6);
      ws.close();
    }

    if (data.type === 'error') {
      setProgressIndex(-1);
      setJobData(`Error: ${data.error}`);
      ws.close();
    }
  };

  return (
    <div>
      {/* URL Input Form */}
      <UrlInputForm ... />
      
      {/* Progress Display - PASS DATA DOWN */}
      <ProgressDisplay 
        progressIndex={progressIndex} 
        jobData={jobData} 
      />
      
      {/* Job Description Display - PASS DATA DOWN */}
      <JobDescriptionDisplay 
        jobData={jobData} 
        onTryAnother={handleTryAnother} 
      />
    </div>
  );
};