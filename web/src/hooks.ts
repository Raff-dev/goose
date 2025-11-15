import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './api/client';
import type { JobResource, RunRequestPayload, TestStatus } from './api/types';

export const useTests = () => {
  return useQuery({
    queryKey: ['tests'],
    queryFn: apiClient.listTests,
  });
};

export const useRuns = () => {
  return useQuery({
    queryKey: ['runs'],
    queryFn: apiClient.listRuns,
    refetchInterval: 500, // Poll every 500ms for faster updates
  });
};

export const useRun = (id: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['runs', id],
    queryFn: () => apiClient.getRun(id),
    enabled: enabled && !!id,
    refetchInterval: enabled && id ? 500 : false, // Poll every 500ms if enabled
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
