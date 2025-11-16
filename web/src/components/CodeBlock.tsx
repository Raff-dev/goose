import React from 'react';
import highlightJSON from '../utils/syntaxHighlight';

interface CodeBlockProps {
  /** Value to render. Can be an object (will be stringified) or a string. */
  value: any;
  /** Optional additional classes applied to the <pre> wrapper */
  className?: string;
}

export default function CodeBlock({ value, className = '' }: CodeBlockProps) {
  const html = highlightJSON(value ?? '');
  return (
    <pre className={`bg-slate-100 text-slate-900 text-xs p-2 rounded overflow-auto ${className}`}>
      <code className="opacity-100" dangerouslySetInnerHTML={{ __html: html }} />
    </pre>
  );
}
