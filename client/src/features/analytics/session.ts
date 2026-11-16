/** A random value for one visit. Not a secret: it only has to differ between visits. */
export function newSessionId(): string {
  const crypto = globalThis.crypto;
  if (typeof crypto?.randomUUID === "function") return crypto.randomUUID();
  return Array.from({ length: 4 }, () => Math.random().toString(16).slice(2, 10).padEnd(8, "0")).join("-");
}

/**
 * The id of this visit: made the first time it is asked for and kept only in memory, so closing the tab or the
 * app ends the visit. Nothing is written to cookies or storage, and it is not tied to a person.
 */
export function createSession(generate: () => string = newSessionId): () => string {
  let id: string | undefined;
  return () => (id ??= generate());
}

export const sessionId = createSession();
