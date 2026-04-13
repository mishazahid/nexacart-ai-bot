import React from 'react';
import clsx from 'clsx';
import {
  formatConfidence,
  getConfidenceLevel,
  getConfidenceColor,
} from '../utils/helpers';

/**
 * Pill-shaped badge showing the confidence level for an assistant response.
 *
 * @param {{ score: number, isFallback: boolean }} props
 */
export default function ConfidenceBadge({ score, isFallback }) {
  if (isFallback) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-surface-100 text-surface-500 border-surface-200">
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
        Escalated to Support
      </span>
    );
  }

  const level = getConfidenceLevel(score);
  const colorClasses = getConfidenceColor(level);
  const pct = Math.round(score * 100);

  const label =
    level === 'high'
      ? 'High Confidence'
      : level === 'medium'
      ? 'Medium Confidence'
      : 'Low Confidence';

  // SVG circular progress indicator
  const radius = 5;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
        colorClasses
      )}
    >
      {/* Mini circular progress */}
      <svg width="14" height="14" viewBox="0 0 14 14" className="flex-shrink-0">
        <circle
          cx="7"
          cy="7"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeOpacity="0.2"
          strokeWidth="2"
        />
        <circle
          cx="7"
          cy="7"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform="rotate(-90 7 7)"
          className="confidence-ring"
        />
      </svg>
      {formatConfidence(score)} {label}
    </span>
  );
}
