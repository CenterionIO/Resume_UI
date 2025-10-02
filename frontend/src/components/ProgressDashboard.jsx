import React, { useState } from 'react';

const ProgressDashboard = ({ progress, jobAnalysis, selectedBullets, enhancedBullets }) => {
  const [expandedSteps, setExpandedSteps] = useState({});

  const toggleStepDetails = (index) => {
    setExpandedSteps(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const getStepIcon = (step) => {
  // Handle both old and new message formats
  const message = step.message || step.data?.message || '';
  
  if (!message) return '⏳';
  
  if (message.includes('Error')) return '❌';
  if (message.includes('Complete')) return '✅';
  if (message.includes('Starting')) return '🚀';
  if (message.includes('Extracting')) return '📄';
  if (message.includes('Analyzing')) return '🔍';
  if (message.includes('Finding')) return '🎯';
  if (message.includes('Enhancing')) return '✨';
  if (message.includes('Assembling')) return '📝';
  if (message.includes('processing')) return '⚙️';
  if (message.includes('scraping')) return '🔍';
  return '⏳';
};

  return (
    <div className="progress-dashboard">
      <div className="progress-timeline">
        {progress.map((step, index) => (
          <div key={step.id || index} className={`timeline-step ${step.status || 'active'}`}>
            <div className="step-icon">{getStepIcon(step)}</div>
            <div className="step-message">{step.message || step.data?.message || 'Processing...'}</div>
            <div className="step-content">
              <div className="step-message">{step.message}</div>
              <div className="step-time">{step.timestamp}</div>
              {step.data && (
                <button 
                  className="toggle-details"
                  onClick={() => toggleStepDetails(index)}
                >
                  {expandedSteps[index] ? 'Hide Details' : 'View Details'}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Job Analysis Details */}
      {jobAnalysis && expandedSteps[1] && (
        <div className="details-panel">
          <h4>Job Analysis</h4>
          <div className="analysis-grid">
            <div className="analysis-item">
              <label>Title:</label>
              <span>{jobAnalysis.job_title}</span>
            </div>
            <div className="analysis-item">
              <label>Level:</label>
              <span>{jobAnalysis.experience_level}</span>
            </div>
            <div className="analysis-item">
              <label>Key Skills:</label>
              <div className="skills-list">
                {jobAnalysis.required_skills?.map(skill => (
                  <span key={skill} className="skill-tag">{skill}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Selected Bullets Details */}
      {selectedBullets && expandedSteps[2] && (
        <div className="details-panel">
          <h4>Selected Experience Bullets</h4>
          <div className="bullets-comparison">
            {selectedBullets.map((bullet, index) => (
              <div key={bullet.id} className="bullet-item">
                <div className="bullet-original">
                  <strong>Original:</strong> {bullet.original_content}
                </div>
                {enhancedBullets?.[index] && (
                  <div className="bullet-enhanced">
                    <strong>Enhanced:</strong> {enhancedBullets[index].enhanced_content}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgressDashboard;