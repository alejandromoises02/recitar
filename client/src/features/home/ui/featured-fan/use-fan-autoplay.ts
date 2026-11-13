import { useCallback, useEffect, useRef, useState } from "react";
import { Easing, cancelAnimation, useReducedMotion, useSharedValue, withTiming } from "react-native-reanimated";
import { scheduleOnRN, scheduleOnUI } from "react-native-worklets";
import { AUTOPLAY_MS } from "./featured.constants";

/**
 * Calls `onAdvance` every AUTOPLAY_MS while running; `progress` (0..1) drives the card's bar and
 * starts over whenever `current` changes. `stop` ends autoplay for good; `toggle` pauses or restarts it.
 */
export function useFanAutoplay(onAdvance: () => void, enabled: boolean, current: number) {
  const reduced = useReducedMotion();
  const [stopped, setStopped] = useState(reduced);
  const [paused, setPaused] = useState(false);
  const progress = useSharedValue(0);
  const shownFor = useRef(current);
  const running = enabled && !stopped && !paused;

  useEffect(() => {
    const reset = shownFor.current !== current;
    shownFor.current = current;
    if (!running) {
      if (reset) progress.set(0);
      cancelAnimation(progress);
      return;
    }
    // Reset and read on the UI thread: a JS-side get() right after set() still returns the old value.
    scheduleOnUI(() => {
      "worklet";
      const from = reset ? 0 : progress.get();
      progress.set(from);
      progress.set(
        withTiming(1, { duration: (1 - from) * AUTOPLAY_MS, easing: Easing.linear }, (finished) => {
          if (finished) scheduleOnRN(onAdvance);
        }),
      );
    });
    return () => cancelAnimation(progress);
  }, [running, current, progress, onAdvance]);

  const stop = useCallback(() => {
    setStopped(true);
    progress.set(0);
  }, [progress]);

  const toggle = useCallback(() => {
    if (stopped) {
      progress.set(0);
      setStopped(false);
      setPaused(false);
    } else {
      setPaused((p) => !p);
    }
  }, [stopped, progress]);

  return { progress, active: running, stop, toggle };
}
