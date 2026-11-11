import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "../features/events/infrastructure/events-api";

export const MAX_RETRIES = 2;
/** Events change when the scraper runs (a few times a day), so a few minutes old is fine. */
const STALE_TIME_MS = 5 * 60 * 1000;

/** Retry what can get better on its own (network, timeouts, rate limits, server errors). */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (failureCount >= MAX_RETRIES) return false;
  if (error instanceof ApiError) {
    return error.status === 408 || error.status === 429 || error.status >= 500;
  }
  return true;
}

export function createQueryClient(): QueryClient {
  return new QueryClient({ defaultOptions: { queries: { retry: shouldRetry, staleTime: STALE_TIME_MS } } });
}
