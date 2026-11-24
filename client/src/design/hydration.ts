import { useSyncExternalStore } from "react";
import type { ScaledSize } from "react-native";
import { useWindowDimensions } from "react-native";

const subscribeNever = () => () => undefined;

/**
 * False while the browser hydrates the web build's pre-rendered page, true from then on (and always in
 * the native apps). The first browser render must match that page, which was made without a browser.
 */
export function useHydrated(): boolean {
  return useSyncExternalStore(subscribeNever, () => true, () => false);
}

/** What the pre-rendered page was made with: no window, so 0 by 0 (the phone layout). */
const PRE_RENDERED: ScaledSize = { width: 0, height: 0, scale: 1, fontScale: 1 };

/**
 * useWindowDimensions, except while hydrating, when it is the size the page was pre-rendered at: a
 * layout chosen from the real width would differ from the pre-rendered HTML, and React would throw the
 * whole page away and paint it again. The real size applies right after.
 */
export function useWindowSize(): ScaledSize {
  const real = useWindowDimensions();
  return useHydrated() ? real : PRE_RENDERED;
}
