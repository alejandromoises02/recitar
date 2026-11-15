import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing } from "../../../design/tokens";

export const styles = StyleSheet.create({
  frame: { width: "100%", overflow: "hidden", borderRadius: radius.card, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.imageFallback },
  fill: StyleSheet.absoluteFill,
  fallback: { alignItems: "center", justifyContent: "center" },
  initials: { fontFamily: fontFamily.display, fontSize: 56, color: colors.text },
  credit: {
    position: "absolute",
    left: spacing.sm,
    bottom: spacing.sm,
    maxWidth: "90%",
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: radius.pill,
    backgroundColor: colors.badge,
  },
  creditText: { fontFamily: fontFamily.body, fontSize: 11.5, color: colors.textMuted },
  creditLink: { color: colors.text, textDecorationLine: "underline" },
});
