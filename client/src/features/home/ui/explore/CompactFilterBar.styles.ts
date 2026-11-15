import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, typography } from "../../../../design/tokens";
import { MIN_TARGET } from "./explore.constants";

export const styles = StyleSheet.create({
  bar: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingVertical: spacing.xs,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
    backgroundColor: colors.background,
  },
  search: { flex: 1 },
  button: {
    height: MIN_TARGET,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.pill,
  },
  buttonActive: { backgroundColor: colors.accent, borderColor: colors.accent },
  pressed: { opacity: 0.7 },
  buttonText: { fontFamily: fontFamily.bodyStrong, fontSize: typography.bodySmall.size.min, color: colors.text },
  buttonTextActive: { color: colors.onAccent },
});
