import { StyleSheet } from "react-native";
import { colors } from "../../../../design/tokens";
import { TINT_OPACITY, TINT_OVERFLOW } from "./PageTint.constants";

export const styles = StyleSheet.create({
  tint: { ...StyleSheet.absoluteFill, overflow: "hidden" },
  image: {
    position: "absolute",
    top: TINT_OVERFLOW,
    bottom: TINT_OVERFLOW,
    left: TINT_OVERFLOW,
    right: TINT_OVERFLOW,
    opacity: TINT_OPACITY,
  },
  // Darkens the edges so the colour gathers around the record fan.
  vignette: {
    ...StyleSheet.absoluteFill,
    backgroundImage: `radial-gradient(80% 70% at 68% 45%, transparent, ${colors.background}d9)`,
  },
});
