import { useEffect } from "react";
import { useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withTiming } from "react-native-reanimated";
import { FLIP } from "./board.constants";

/** Row `index` flips down from its top edge after the rows before it; no motion under reduced motion. */
export function useFlipIn(index: number) {
  const reduced = useReducedMotion();
  const angle = useSharedValue(reduced ? 0 : FLIP.startAngle);
  useEffect(() => {
    if (reduced) return;
    angle.value = withDelay(FLIP.firstDelay + index * FLIP.stagger, withTiming(0, { duration: FLIP.duration, easing: FLIP.easing }));
  }, [angle, index, reduced]);
  return useAnimatedStyle(() => ({
    transformOrigin: "top",
    transform: [{ perspective: FLIP.perspective }, { rotateX: `${angle.value}deg` }],
  }));
}
