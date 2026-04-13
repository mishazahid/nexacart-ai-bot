/**
 * Format a confidence score (0–1) as a percentage string.
 *
 * @param {number} score - Confidence score between 0 and 1.
 * @returns {string} e.g. "72%"
 */
export function formatConfidence(score) {
  return `${Math.round(score * 100)}%`;
}

/**
 * Classify a confidence score into a named level.
 *
 * @param {number} score - Confidence score between 0 and 1.
 * @returns {'high'|'medium'|'low'}
 */
export function getConfidenceLevel(score) {
  if (score >= 0.7) return 'high';
  if (score >= 0.4) return 'medium';
  return 'low';
}

/**
 * Return the appropriate Tailwind colour classes for a confidence level.
 *
 * @param {'high'|'medium'|'low'} level
 * @returns {string} Tailwind class string for background + text colour.
 */
export function getConfidenceColor(level) {
  switch (level) {
    case 'high':
      return 'bg-success-100 text-success-700 border-success-300';
    case 'medium':
      return 'bg-warning-100 text-warning-700 border-warning-300';
    case 'low':
    default:
      return 'bg-danger-100 text-danger-700 border-danger-300';
  }
}

/**
 * Format a Date object as a short time string.
 *
 * @param {Date} date
 * @returns {string} e.g. "2:34 PM"
 */
export function formatTimestamp(date) {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

/**
 * Truncate text to a maximum length, appending an ellipsis if truncated.
 *
 * @param {string} text
 * @param {number} maxLength
 * @returns {string}
 */
export function truncateText(text, maxLength) {
  if (!text || text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '…';
}

/**
 * Convert a snake_case filename into a human-readable title.
 * e.g. "shipping_policy.md" → "Shipping Policy"
 *
 * @param {string} filename
 * @returns {string}
 */
export function formatSourceName(filename) {
  return filename
    .replace(/\.md$/i, '')
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
