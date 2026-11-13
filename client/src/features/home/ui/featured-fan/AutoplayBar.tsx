import type { SharedValue } from "react-native-reanimated";
import Animated, { useAnimatedStyle } from "react-native-reanimated";
import { View } from "react-native";
import { styles } from "./AutoplayBar.styles";

export function AutoplayBar({ progress }: { progress: SharedValue<number> }) {
  const fill = useAnimatedStyle(() => ({
    transform: [{ scaleX: progress.get() }],
  }));
  return (
    <View style={styles.track} aria-hidden>
      <Animated.View style={[styles.fill, fill]} />
    </View>
  );
}
