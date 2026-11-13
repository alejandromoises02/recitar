import { View } from "react-native";
import type { SharedValue } from "react-native-reanimated";
import Animated, { useAnimatedStyle } from "react-native-reanimated";
import { FittedImage } from "../media/FittedImage";
import { RECORD_GROOVES, RECORD_HIDDEN_SCALE } from "./featured.constants";
import { recordGeometry, styles } from "./Record.styles";

type Props = {
  size: number;
  travel: number;
  shown: SharedValue<number>;
  photo: string | null;
};

/** The small record that slides out of the centre sleeve; `shown` runs 0 (inside) to 1 (out). */
export function Record({ size, travel, shown, photo }: Props) {
  const motion = useAnimatedStyle(() => ({
    opacity: Math.min(1, shown.get() * 4),
    transform: [
      { translateX: shown.get() * travel },
      { scale: RECORD_HIDDEN_SCALE + (1 - RECORD_HIDDEN_SCALE) * shown.get() },
    ],
  }));
  const geometry = recordGeometry(size);

  return (
    <Animated.View
      style={[styles.record, geometry.record, motion]}
      pointerEvents="none"
    >
      {RECORD_GROOVES.map((share) => (
        <View key={share} style={[styles.groove, geometry.groove(share)]} />
      ))}
      <View style={[styles.label, geometry.label]}>
        {photo ? <FittedImage uri={photo} style={styles.labelImage} /> : null}
        <View style={[styles.hole, geometry.hole]} />
      </View>
    </Animated.View>
  );
}
