/**
 * Extract a user-friendly error message from various error types.
 * Handles Axios errors, standard Error objects, and unknown errors.
 */
export function getErrorMessage(err: unknown): string | null {
  if (!err) return null;

  const axiosError = err as {
    response?: {
      status?: number;
      statusText?: string;
      data?: { detail?: string; message?: string; error?: string } | string;
    };
    message?: string;
  };

  // Try to extract message from response data
  if (axiosError.response?.data) {
    const data = axiosError.response.data;
    if (typeof data === 'string') return data;
    if (data.detail) return data.detail;
    if (data.message) return data.message;
    if (data.error) return data.error;
  }

  // Fall back to HTTP status
  if (axiosError.response?.status) {
    const status = axiosError.response.status;
    const statusText = axiosError.response.statusText || 'Error';
    return `HTTP ${status}: ${statusText}`;
  }

  // Fall back to error message
  if (axiosError.message) return axiosError.message;
  if (err instanceof Error) return err.message;

  return 'An unknown error occurred';
}
