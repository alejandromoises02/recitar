import type { ReactNode } from "react";
import type { StyleProp, ViewStyle } from "react-native";
import { View } from "react-native";
import { styles } from "./Flap.styles";

type Props = { style?: StyleProp<ViewStyle>; children?: ReactNode };

/** A split-flap panel. The hinge sits behind the letters so it never reads as strikethrough. */
export function Flap({ style, children }: Props) {
  return (
    <View style={[styles.flap, style]}>
      <View style={styles.lowerHalf} />
      <View style={styles.hinge} />
      {children}
    </View>
  );
}
