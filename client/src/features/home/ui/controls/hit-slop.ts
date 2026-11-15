import type { Insets } from "react-native";
import { touchTarget } from "../../../../design/tokens";

/**
 * Extra touch area above and below a control shorter than the 44 pt target, so it looks the same and is
 * easier to hit on phones. Web ignores hitSlop: there every control is already at least 24 px (WCAG 2.5.8).
 */
export function verticalSlop(height: number): Insets {
  const extra = Math.max(0, (touchTarget - height) / 2);
  return { top: extra, bottom: extra };
}
