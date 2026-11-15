/**
 * Heading props with a level. A bare accessibilityRole="header" becomes <h1> on web, so every title
 * needs its level for the page outline screen readers navigate by.
 */
export const heading = (level: 1 | 2 | 3) => ({ role: "heading" as const, "aria-level": level });
