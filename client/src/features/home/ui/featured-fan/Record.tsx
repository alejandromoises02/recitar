import { useEffect } from "react";
import { Text, View } from "react-native";
import type { SharedValue } from "react-native-reanimated";
import Animated, { Easing, cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import { FittedImage } from "../media/FittedImage";
import { RECORD_GROOVES, RECORD_HIDDEN_SCALE, RECORD_TURN_MS } from "./featured.constants";
import { recordGeometry, styles } from "./Record.styles";

type Props = {
  size: number;
  travel: number;
  shown: SharedValue<number>;
  photo: string | null;
  /** The show has a Spotify sample: the record is its play button and wears a play badge. */
  playable: boolean;
  playing: boolean;
};

/**
 * The small record that slides out of the centre sleeve; `shown` runs 0 (inside) to 1 (out). It spins
 * only while its sample plays. Taps reach it through the fan's gesture (see FeaturedFan).
 */
export function Record({ size, travel, shown, photo, playable, playing }: Props) {
  const reduced = useReducedMotion();
  const turn = useSharedValue(0);
  const motion = useAnimatedStyle(() => ({
    opacity: Math.min(1, shown.get() * 4),
    transform: [
      { translateX: shown.get() * travel },
      { scale: RECORD_HIDDEN_SCALE + (1 - RECORD_HIDDEN_SCALE) * shown.get() },
    ],
  }));
  const spin = useAnimatedStyle(() => ({ transform: [{ rotate: `${turn.get()}deg` }] }));
  const geometry = recordGeometry(size);

  useEffect(() => {
    if (!playing || reduced) {
      cancelAnimation(turn);
      return;
    }
    const from = turn.get() % 360;
    turn.set(from);
    turn.set(withRepeat(withTiming(from + 360, { duration: RECORD_TURN_MS, easing: Easing.linear }), -1));
    return () => cancelAnimation(turn);
  }, [playing, reduced, turn]);

  return (
    <Animated.View style={[styles.record, geometry.record, motion]} pointerEvents="none">
      <Animated.View style={[styles.disc, spin]}>
        {RECORD_GROOVES.map((share) => (
          <View key={share} style={[styles.groove, geometry.groove(share)]} />
        ))}
        <View style={[styles.label, geometry.label]}>
          {photo ? <FittedImage uri={photo} style={styles.labelImage} /> : null}
          <View style={[styles.hole, geometry.hole]} />
        </View>
      </Animated.View>
      {playable ? (
        <View style={[styles.badge, geometry.badge]} aria-hidden>
          <Text style={[styles.badgeGlyph, geometry.badgeGlyph]}>{playing ? "❚❚" : "▶"}</Text>
        </View>
      ) : null}
    </Animated.View>
  );
}
