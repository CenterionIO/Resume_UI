import React, { useState } from 'react';

const ResumePreview = ({ resume, jobAnalysis }) => {
  const [atsScore, setAtsScore] = useState(null);
  const [keywordMatches, setKeywordMatches] = useState([]);

  const analyzeATSCompatibility = () => {
    if (!resume || !jobAnalysis) return;

    const requiredSkills = jobAnalysis.required_skills || [];
    const resumeText = resume.toLowerCase();
    
    const matches = requiredSkills.filter(skill => 
      resumeText.includes(skill.toLowerCase())
    );
    
    const score = Math.round((matches.length / requiredSkills.length) * 100);
    
    setAtsScore(score);
    setKeywordMatches(matches);
  };

  const highlightKeywords = (text) => {
    if (!jobAnalysis?.required_skills) return text;
    
    let highlightedText = text;
    jobAnalysis.required_skills.forEach(skill => {
      const regex = new RegExp(`\\b${skill}\\b`, 'gi');
      highlightedText = highlightedText.replace(
        regex, 
        '<mark class="keyword-match">$&</mark>'
      );
    });
    
    return { __html: highlightedText };
  };

  return (
    <div className="resume-preview">
      <div className="preview-header">
        <h3>Generated Resume</h3>
        
        {atsScore !== null && (
          <div className="ats-score">
            <div className={`score-circle ${atsScore >= 80 ? 'excellent' : atsScore >= 60 ? 'good' : 'poor'}`}>
              {atsScore}%
            </div>
            <span>ATS Match Score</span>
          </div>
        )}
      </div>

      <div className="preview-actions">
        <button onClick={analyzeATSCompatibility} className="btn-secondary">
          Analyze ATS Compatibility
        </button>
        <button 
          onClick={() => navigator.clipboard.writeText(resume)}
          className="btn-primary"
        >
          Copy to Clipboard
        </button>
        <button onClick={() => window.print()} className="btn-secondary">
          Print/PDF
        </button>
      </div>

      {keywordMatches.length > 0 && (
        <div className="keyword-analysis">
          <h4>Keyword Matches Found:</h4>
          <div className="keyword-tags">
            {keywordMatches.map(keyword => (
              <span key={keyword} className="keyword-tag matched">
                {keyword} ✓
              </span>
            ))}
            {jobAnalysis.required_skills
              .filter(skill => !keywordMatches.includes(skill))
              .map(keyword => (
                <span key={keyword} className="keyword-tag missing">
                  {keyword} ✗
                </span>
              ))
            }
          </div>
        </div>
      )}

      <div 
        className="resume-content"
        dangerouslySetInnerHTML={highlightKeywords(resume)}
      />
    </div>
  );
};

export default ResumePreview;