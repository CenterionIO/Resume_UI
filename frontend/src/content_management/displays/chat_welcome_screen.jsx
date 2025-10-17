import React from 'react';

const Chat_Welcome_Screen = ({ onSubmit }) => {
  const styles = {
    container: {
      width: '100%',
      maxWidth: '56rem',
      backgroundColor: 'white',
      borderRadius: '0.75rem',
      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
      overflow: 'hidden'
    },
    innerContainer: {
      padding: '2rem',
      width: '100%'
    },
    form: {
      marginBottom: '1.5rem'
    },
    supportedSites: {
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      marginBottom: '2rem',
      marginLeft: '0.5rem'
    },
    supportedText: {
      fontSize: '0.875rem',
      color: '#6b7280',
      whiteSpace: 'nowrap'
    },
    tagsContainer: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: '0.75rem'
    },
    tag: {
      padding: '0.25rem 0.75rem',
      backgroundColor: '#f3f4f6',
      borderRadius: '0.5rem',
      border: '1px solid #e5e7eb',
      fontSize: '0.875rem'
    },
    featuresContainer: {
      backgroundColor: '#f9fafb',
      padding: '1.5rem',
      borderRadius: '0.5rem'
    },
    featuresTitle: {
      fontSize: '1.125rem',
      fontWeight: '500',
      marginBottom: '1rem'
    },
    featuresGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: '0.75rem',
      fontSize: '0.875rem'
    },
    featureItem: {
      display: 'flex',
      alignItems: 'center'
    },
    checkmark: {
      width: '1rem',
      height: '1rem',
      marginRight: '0.5rem',
      color: '#10b981'
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.innerContainer}>
        <div style={styles.form}>
          {onSubmit && <UrlInputForm onSubmit={onSubmit} />}
        </div>

        <div style={styles.supportedSites}>
          <p style={styles.supportedText}>Supported job platforms:</p>
          <div style={styles.tagsContainer}>
            <span style={styles.tag}>LinkedIn</span>
            <span style={styles.tag}>Indeed</span>
            <span style={styles.tag}>Glassdoor</span>
            <span style={styles.tag}>AngelList</span>
            <span style={styles.tag}>Wellfound</span>
          </div>
        </div>

        <div style={styles.featuresContainer}>
          <h3 style={styles.featuresTitle}>Features</h3>
          <div style={styles.featuresGrid}>
            <div style={styles.featureItem}>
              <span style={styles.checkmark}>✓</span>
              ATS optimization
            </div>
            <div style={styles.featureItem}>
              <span style={styles.checkmark}>✓</span>
              Keyword matching
            </div>
            <div style={styles.featureItem}>
              <span style={styles.checkmark}>✓</span>
              Bullet enhancement
            </div>
            <div style={styles.featureItem}>
              <span style={styles.checkmark}>✓</span>
              Skills alignment
            </div>
            <div style={styles.featureItem}>
              <span style={styles.checkmark}>✓</span>
              Format perfecting
            </div>
            <div style={styles.featureItem}>
              <span style={styles.checkmark}>✓</span>
              Industry phrasing
            </div>
            <div style={styles.featureItem}>
              <span style={styles.checkmark}>✓</span>
              Experience matching
            </div>
            <div style={styles.featureItem}>
              <span style={styles.checkmark}>✓</span>
              Education optimization
            </div>
            <div style={styles.featureItem}>
              <span style={styles.checkmark}>✓</span>
              Certification alignment
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat_Welcome_Screen;