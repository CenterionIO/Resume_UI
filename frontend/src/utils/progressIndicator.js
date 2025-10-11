/**
 * Progress Indicator Configuration
 *
 * This module defines all the progress messages shown during the scraping process.
 * Update these messages to customize what users see at each step.
 */

export const progressMessages = {
  // Initial connection
  connecting: "Testing backend connection...",

  // WebSocket connected
  connected: "✅ WebSocket connected",

  // Starting login process
  authenticating: "🔐 Starting LinkedIn login...",

  // Login successful
  authenticated: "✅ Login successful",

  // Navigating to job page
  navigating: "🌐 Navigating to job...",

  // Parsing job content
  parsing: "✅ Parsing complete",

  // Scraping completed
  complete: "✅ Scraping completed!",

  // Error states
  connectionFailed: "❌ WebSocket connection failed",
  scrapingError: "❌ Scraping error:",

  // Fallback/default
  starting: "Starting...",
};

/**
 * Get a custom progress message
 * @param {string} key - The message key from progressMessages
 * @param {string} customText - Optional custom text to append
 * @returns {string} The formatted progress message
 */
export const getProgressMessage = (key, customText = '') => {
  const baseMessage = progressMessages[key] || progressMessages.starting;
  return customText ? `${baseMessage} ${customText}` : baseMessage;
};

export default progressMessages;
