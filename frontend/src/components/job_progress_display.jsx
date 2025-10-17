import React, { useState, useEffect } from 'react';

/**
 * Job Progress Display - Self-contained progress experience module
 *
 * This module owns ALL progress update logic and presentation.
 * It manages its own phrase sequences, timing, and user experience.
 *
 * Future: Can be configured via admin panel or external config file.
 */

// =============================================================================
// CONFIGURATION - Easy to edit phrase sequences
// =============================================================================

const PHRASE_CONFIGS = {
  single_scrape: {
    estimatedDuration: 8000, // 8 seconds total
    phrases: [
      "Hang tight, we're on it! 🚀",
      "LinkedIn login successful ✅",
      "Working my magic... ✨",
      "Fetching job details... 📄",
      "Almost there! 🎯",
      "Everything is looking good! 👌"
    ]
  },

  bulk_scrape: {
    estimatedDuration: 30000, // 30 seconds total
    phrases: [
      "Initiating bulk search... 🔍",
      "Connecting to LinkedIn... 🌐",
      "Login successful! ✅",
      "Searching through listings... 📊",
      "Found some great matches! 🎯",
      "Gathering job details... 📝",
      "Processing data... ⚙️",
      "Almost done! 🚀",
      "Wrapping things up... 🎁",
      "All set! 👌"
    ]
  },

  // Placeholder for future scrape types
  indeed_scrape: {
    estimatedDuration: 10000,
    phrases: [
      "Connecting to Indeed... 🌐",
      "Fetching job data... 📄",
      "Processing results... ⚙️",
      "Done! ✅"
    ]
  }
};

// =============================================================================
// COMPONENT
// =============================================================================

const Job_Progress_Display = ({
  scrapeType = 'single_scrape',  // 'single_scrape', 'bulk_scrape', etc.
  isActive = false,               // Start the phrase sequence
  onSequenceComplete,             // Callback when phrase sequence finishes
  realtimeHooks = {}              // PLACEHOLDER: Future real-time event hooks
}) => {
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [isSequenceRunning, setIsSequenceRunning] = useState(false);

  const config = PHRASE_CONFIGS[scrapeType] || PHRASE_CONFIGS.single_scrape;
  const { phrases, estimatedDuration } = config;
  const intervalDuration = estimatedDuration / phrases.length;

  // PLACEHOLDER: Future real-time event hooks
  // Example usage when implemented:
  // realtimeHooks = {
  //   onLoginSuccess: () => jumpToPhrase(1),
  //   onDataFetched: () => jumpToPhrase(4),
  //   onError: () => showErrorPhrase()
  // }

  useEffect(() => {
    if (!isActive) return;

    // Reset and start sequence
    setCurrentPhraseIndex(0);
    setIsSequenceRunning(true);

    // Fixed interval phrase progression
    const timer = setInterval(() => {
      setCurrentPhraseIndex(prev => {
        const nextIndex = prev + 1;

        // Check if sequence complete
        if (nextIndex >= phrases.length) {
          clearInterval(timer);
          setIsSequenceRunning(false);

          // Notify parent that sequence is complete
          if (onSequenceComplete) {
            onSequenceComplete();
          }

          return prev; // Stay on last phrase
        }

        return nextIndex;
      });
    }, intervalDuration);

    return () => {
      clearInterval(timer);
    };
  }, [isActive, phrases.length, intervalDuration, onSequenceComplete]);

  // Reset when isActive becomes false
  useEffect(() => {
    if (!isActive) {
      setCurrentPhraseIndex(0);
      setIsSequenceRunning(false);
    }
  }, [isActive]);

  if (!isActive) return null;

  const currentPhrase = phrases[currentPhraseIndex] || phrases[0];

  return (
    <div style={{
      width: '100%',
      maxWidth: '48rem',
      flex: 1,
      overflowY: 'auto',
      marginBottom: '1rem',
      textAlign: 'left',
      paddingLeft: '1rem'
    }}>
      <div style={{
        background: 'linear-gradient(90deg, #ffffff, #d1d5db, #ffffff)',
        backgroundSize: '200% 200%',
        WebkitBackgroundClip: 'text',
        backgroundClip: 'text',
        color: 'transparent',
        animation: 'gradientAnimation 3s ease infinite',
        padding: '0.5rem 1rem',
        borderRadius: '0.5rem',
        display: 'inline-block',
        fontSize: '1.125rem',
        fontWeight: '500'
      }}>
        {currentPhrase}
      </div>

      {/* Debug info - remove in production */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{
          marginTop: '0.5rem',
          fontSize: '0.75rem',
          color: 'rgba(255,255,255,0.5)'
        }}>
          Phrase {currentPhraseIndex + 1}/{phrases.length} |
          Type: {scrapeType} |
          Interval: {(intervalDuration / 1000).toFixed(1)}s
        </div>
      )}
    </div>
  );
};

export default Job_Progress_Display;

// =============================================================================
// FUTURE ENHANCEMENTS (Admin Config)
// =============================================================================

/**
 * Future: Load phrase configs from external source
 *
 * export const loadPhraseConfig = async () => {
 *   const response = await fetch('/api/admin/phrase-config');
 *   return response.json();
 * };
 *
 * This allows non-developers to update phrases via admin panel.
 */
