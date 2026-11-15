import type { ReactNode } from "react";
import type { StyleProp, ViewProps, ViewStyle } from "react-native";
import { View } from "react-native";
import { styles } from "./Flap.styles";

type Props = { style?: StyleProp<ViewStyle>; role?: ViewProps["role"]; children?: ReactNode };

/** A split-flap panel. The hinge sits behind the letters so it never reads as strikethrough. */
export function Flap({ style, role, children }: Props) {
  return (
    <View style={[styles.flap, style]} role={role}>
      <View style={styles.lowerHalf} />
      <View style={styles.hinge} />
      {children}
    </View>
  );
}
