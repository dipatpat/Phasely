import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";
import { clearToken, getToken } from "../auth/tokenStorage";
import { ApiError } from "./client";

function handleError(error: Error) {
  if (
    error instanceof ApiError &&
    error.status === 401 &&
    getToken() !== null
  ) {
    clearToken();
    window.location.assign("/login");
  }
}

export const queryClient = new QueryClient({
  queryCache: new QueryCache({ onError: handleError }),
  mutationCache: new MutationCache({ onError: handleError }),
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (failureCount, error) =>
        !(error instanceof ApiError && error.status < 500) && failureCount < 2,
    },
  },
});
