import { StyleSheet } from "react-native";
import type { ViewStyle } from "react-native";
import { colors, radius, spacing } from "../../../../design/tokens";

export const hingeLine: ViewStyle = {
  position: "absolute",
  left: 0,
  right: 0,
  top: "50%",
  height: 1,
  marginTop: -0.5,
  backgroundColor: colors.flapHinge,
};

export const styles = StyleSheet.create({
  flap: {
    justifyContent: "center",
    paddingHorizontal: spacing.xs,
    paddingVertical: spacing.hair,
    borderRadius: radius.flap,
    backgroundColor: colors.flapTop,
    overflow: "hidden",
  },
  lowerHalf: { position: "absolute", left: 0, right: 0, top: "50%", bottom: 0, backgroundColor: colors.flapBottom },
  hinge: hingeLine,
});
