function escapeHtml(unsafe: string) {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Return an HTML string with basic JSON syntax highlighting.
 * Uses a single regex-based tokenizer pass to avoid nested/overlapping
 * replacements that can corrupt output.
 */
export function highlightJSON(obj: any) {
  let json: string;
  try {
    json = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
  } catch (e) {
    json = String(obj);
  }

  const tokenized = json.replace(/("(?:\\.|[^"\\])*"\s*:?)|\b(true|false|null)\b|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g, (match, str, bool, num) => {
    if (str !== undefined) {
      // Determine if this is a key (ends with colon after optional whitespace)
      if (/:\s*$/.test(str)) {
        return `<span class="text-rose-500">${escapeHtml(str)}</span>`;
      }
      return `<span class="text-emerald-500">${escapeHtml(str)}</span>`;
    }
    if (bool !== undefined) {
      return `<span class="text-indigo-500">${escapeHtml(bool)}</span>`;
    }
    if (num !== undefined) {
      return `<span class="text-violet-500">${escapeHtml(num)}</span>`;
    }
    return escapeHtml(match);
  });

  // Also highlight bare nulls (in case they didn't match above) — keep idempotent
  return tokenized.replace(/\bnull\b/g, '<span class="text-slate-500">null</span>');
}

export default highlightJSON;
