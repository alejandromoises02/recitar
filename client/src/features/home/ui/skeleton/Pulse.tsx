import type { ReactNode } from "react";
import { useEffect } from "react";
import type { StyleProp, ViewStyle } from "react-native";
import Animated, { Easing, cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import { motion } from "../../../../design/tokens";

type Props = { style?: StyleProp<ViewStyle>; children?: ReactNode };

/** A loading placeholder that fades down and back up until it unmounts; still when the system asks for less motion. */
export function Pulse({ style, children }: Props) {
  const reduced = useReducedMotion();
  const opacity = useSharedValue(1);

  useEffect(() => {
    if (reduced) return;
    const half = { duration: motion.signature.skeletonPulse / 2, easing: Easing.bezier(...motion.easing.inOut) };
    opacity.set(withRepeat(withTiming(motion.skeletonPulseMin, half), -1, true));
    return () => cancelAnimation(opacity);
  }, [reduced, opacity]);

  const faded = useAnimatedStyle(() => ({ opacity: opacity.get() }));
  return (
    <Animated.View style={[style, faded]} aria-hidden>
      {children}
    </Animated.View>
  );
}
