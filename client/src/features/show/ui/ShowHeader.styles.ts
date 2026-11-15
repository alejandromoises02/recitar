import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, touchTarget } from "../../../design/tokens";

export const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md, paddingVertical: spacing.md },
  back: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    minHeight: touchTarget,
    minWidth: touchTarget,
    justifyContent: "center",
    paddingHorizontal: spacing.sm,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
  },
  pressed: { backgroundColor: colors.line },
  chevron: { fontFamily: fontFamily.bodyStrong, fontSize: 22, lineHeight: 24, color: colors.text },
  backText: { fontFamily: fontFamily.body, fontSize: 13, color: colors.text },
  end: { marginLeft: "auto" },
});
