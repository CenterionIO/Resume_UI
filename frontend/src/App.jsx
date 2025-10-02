// src/App.jsx
import { useState } from 'react';
import UrlInput from './components/UrlInput';
import './App.css';

function App() {
  const [isSubmitted, setIsSubmitted] = useState(false);

  return (
    <div className="app">
      <UrlInput onSubmissionChange={setIsSubmitted} isSubmitted={isSubmitted} />
    </div>
  );
}

export default App;