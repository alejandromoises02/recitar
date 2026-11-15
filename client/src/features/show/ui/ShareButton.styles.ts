import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, touchTarget } from "../../../design/tokens";

export const styles = StyleSheet.create({
  wrap: { alignItems: "center", gap: spacing.hair },
  button: {
    width: touchTarget,
    height: touchTarget,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
  },
  pressed: { backgroundColor: colors.line },
  copied: { fontFamily: fontFamily.body, fontSize: 11, color: colors.textMuted },
  hidden: { opacity: 0 },
});
