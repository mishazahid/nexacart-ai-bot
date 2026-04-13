import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { formatSourceName } from '../utils/helpers';

/**
 * Collapsible card showing a knowledge base source reference.
 *
 * @param {{ source: { filename: string, chunk_preview: string, score: number } }} props
 */
export default function SourceCard({ source }) {
  const [expanded, setExpanded] = useState(false);

  const filledDots = Math.round(source.score * 5);

  return (
    <div className="source-card border border-surface-200 rounded-lg overflow-hidden text-xs bg-surface-50 hover:border-surface-300 transition-colors">
      {/* Header row — always visible */}
      <button
        onClick={() => setExpanded((prev) => !prev)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-surface-100 transition-colors"
        aria-expanded={expanded}
      >
        <FileText size={13} className="text-surface-400 flex-shrink-0" />

        <span className="flex-1 font-medium text-surface-700 truncate">
          {formatSourceName(source.filename)}
        </span>

        {/* Dot score */}
        <span className="flex items-center gap-0.5 mr-1" aria-label={`Score ${source.score.toFixed(2)}`}>
          {Array.from({ length: 5 }).map((_, i) => (
            <span
              key={i}
              className={
                i < filledDots
                  ? 'text-primary-500'
                  : 'text-surface-300'
              }
            >
              ●
            </span>
          ))}
        </span>

        {expanded ? (
          <ChevronUp size={13} className="text-surface-400 flex-shrink-0" />
        ) : (
          <ChevronDown size={13} className="text-surface-400 flex-shrink-0" />
        )}
      </button>

      {/* Expandable body */}
      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t border-surface-200">
          <p className="text-surface-600 italic leading-relaxed">
            "{source.chunk_preview}"
          </p>
        </div>
      )}
    </div>
  );
}
