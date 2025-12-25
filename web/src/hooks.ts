import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { API_BASE_URL, apiClient } from './api/client';
import type { JobResource, RunRequestPayload, TestResultModel, TestStatus } from './api/types';

type RunsStreamMessage =
  | { type: 'snapshot'; jobs: JobResource[] }
  | { type: 'job'; job: JobResource };

const sortRuns = (runs: JobResource[]): JobResource[] => {
  return [...runs].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
};

const buildRunsWebSocketUrl = (): string | null => {
  try {
    const url = new URL(API_BASE_URL);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    const trimmedPath = url.pathname.replace(/\/+$/, '');
    url.pathname = `${trimmedPath}/testing/ws/runs`.replace(/\/{2,}/g, '/');
    url.search = '';
    url.hash = '';
    return url.toString();
  } catch {
    return null;
  }
};

export const useTests = () => {
  return useQuery({
    queryKey: ['tests'],
    queryFn: apiClient.listTests,
    retry: false, // Don't retry on 4xx errors - show immediately
  });
};

export const useRuns = () => {
  const queryClient = useQueryClient();
  const queryResult = useQuery({
    queryKey: ['runs'],
    queryFn: apiClient.listRuns,
    refetchInterval: false,
  });

  useEffect(() => {
    if (typeof window === 'undefined' || !('WebSocket' in window)) {
      return;
    }

    const socketUrl = buildRunsWebSocketUrl();
    if (!socketUrl) {
      return;
    }

    let ws: WebSocket | null = null;
    let shouldReconnect = true;
    let retryHandle: number | null = null;

    const handleMessage = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as RunsStreamMessage;
        if (payload.type === 'snapshot') {
          const jobs = sortRuns(payload.jobs || []);
          queryClient.setQueryData(['runs'], jobs);
          jobs.forEach(job => {
            queryClient.setQueryData(['runs', job.id], job);
          });
        } else if (payload.type === 'job' && payload.job) {
          const job = payload.job;
          queryClient.setQueryData(['runs'], (current: JobResource[] | undefined) => {
            const next = (current || []).filter(item => item.id !== job.id);
            next.push(job);
            return sortRuns(next);
          });
          queryClient.setQueryData(['runs', job.id], job);

          // When a job completes (succeeded/failed), invalidate test history for affected tests
          // so that TestDetail components show accurate history counts
          if (job.status === 'succeeded' || job.status === 'failed') {
            for (const result of job.results) {
              queryClient.invalidateQueries({ queryKey: ['history', result.qualified_name] });
            }
            // Also invalidate the global history
            queryClient.invalidateQueries({ queryKey: ['history'] });
          }
        }
      } catch (err) {
        console.error('Failed to process runs websocket payload', err);
      }
    };

    const connect = () => {
      ws = new WebSocket(socketUrl);
      ws.onmessage = handleMessage;
      ws.onerror = () => {
        ws?.close();
      };
      ws.onclose = () => {
        if (shouldReconnect) {
          retryHandle = window.setTimeout(connect, 2000);
        }
      };
    };

    connect();

    return () => {
      shouldReconnect = false;
      if (retryHandle !== null) {
        window.clearTimeout(retryHandle);
      }
      ws?.close();
    };
  }, [queryClient]);

  return queryResult;
};

export const useRun = (id: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['runs', id],
    queryFn: () => apiClient.getRun(id),
    enabled: enabled && !!id,
    refetchInterval: false,
  });
};

export const useCreateRun = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload?: RunRequestPayload) => apiClient.createRun(payload),
    onMutate: async (payload) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['runs'] });

      // Snapshot the previous value
      const previousRuns = queryClient.getQueryData(['runs']);

      // Create optimistic test statuses - all tests start as 'queued'
      const testStatuses: Record<string, TestStatus> = {};
      const testNames = payload?.tests || [];

      if (testNames.length > 0) {
        // Set specific tests to queued
        testNames.forEach(name => {
          testStatuses[name] = 'queued';
        });
      }

      const tempId = `temp-${Date.now()}`;

      // Optimistically update to the new value
      const optimisticJob: JobResource = {
        id: tempId, // Temporary ID
        status: 'queued',
        tests: testNames,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        error: null,
        results: [],
        test_statuses: testStatuses
      };

      queryClient.setQueryData(['runs'], (old: JobResource[] | undefined) => [optimisticJob, ...(old || [])]);

      // Return a context object with the snapshotted value
      return { previousRuns, tempId };
    },
    onSuccess: (job, payload, context) => {
      // Replace the optimistic job with the real one
      queryClient.setQueryData(['runs'], (old: JobResource[] | undefined) => {
        if (!old) return [job];
        return old.map(j => j.id === context?.tempId ? job : j);
      });
    },
    onError: (err, payload, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousRuns) {
        queryClient.setQueryData(['runs'], context.previousRuns);
      }
    },
  });
};

export const useHistory = () => {
  return useQuery({
    queryKey: ['history'],
    queryFn: apiClient.getHistory,
    retry: false,
  });
};

export const useTestHistory = (qualifiedName: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['history', qualifiedName],
    queryFn: () => apiClient.getTestHistory(qualifiedName),
    enabled: enabled && !!qualifiedName,
    retry: false,
  });
};

export const useClearHistory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.clearHistory(),
    onSuccess: () => {
      // Clear the history cache and refetch
      queryClient.setQueryData(['history'], {});
      // Also clear runs since we're resetting state
      queryClient.setQueryData(['runs'], []);
    },
  });
};

export const useClearTestHistory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (qualifiedName: string) => apiClient.clearTestHistory(qualifiedName),
    onSuccess: (_, qualifiedName) => {
      // Clear the test-specific history cache
      queryClient.setQueryData(['history', qualifiedName], []);
      // Remove from global history cache
      queryClient.setQueryData(['history'], (old: Record<string, TestResultModel> | undefined) => {
        if (!old) return {};
        const next = { ...old };
        delete next[qualifiedName];
        return next;
      });
    },
  });
};

export const useDeleteTestRun = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ qualifiedName, index }: { qualifiedName: string; index: number }) =>
      apiClient.deleteTestRun(qualifiedName, index),
    onSuccess: (_, { qualifiedName }) => {
      // Invalidate the test-specific history to refetch
      queryClient.invalidateQueries({ queryKey: ['history', qualifiedName] });
      // Invalidate global history too
      queryClient.invalidateQueries({ queryKey: ['history'] });
    },
  });
};
