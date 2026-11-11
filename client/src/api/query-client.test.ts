import { describe, expect, it } from "vitest";
import { ApiError } from "../features/events/infrastructure/events-api";
import { MAX_RETRIES, createQueryClient, shouldRetry } from "./query-client";

const apiError = (status: number) => new ApiError(status, "x", null);

describe("shouldRetry", () => {
  it.each([400, 404, 422])("does not retry a %i: asking again gives the same answer", (status) => {
    expect(shouldRetry(0, apiError(status))).toBe(false);
  });

  it.each([408, 429, 500, 502, 503])("retries a %i a couple of times", (status) => {
    expect(shouldRetry(0, apiError(status))).toBe(true);
    expect(shouldRetry(MAX_RETRIES - 1, apiError(status))).toBe(true);
    expect(shouldRetry(MAX_RETRIES, apiError(status))).toBe(false);
  });

  it("retries a network failure", () => {
    expect(shouldRetry(0, new TypeError("Network request failed"))).toBe(true);
    expect(shouldRetry(MAX_RETRIES, new TypeError("Network request failed"))).toBe(false);
  });
});

describe("createQueryClient", () => {
  it("uses shouldRetry and keeps data fresh for a while", () => {
    const defaults = createQueryClient().getDefaultOptions().queries;
    expect(defaults?.retry).toBe(shouldRetry);
    expect(defaults?.staleTime).toBe(5 * 60 * 1000);
  });
});
