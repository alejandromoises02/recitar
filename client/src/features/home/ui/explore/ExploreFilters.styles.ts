import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, typography } from "../../../../design/tokens";
import { labelText } from "../home.styles";

export const styles = StyleSheet.create({
  panel: { gap: 14, padding: spacing.md, borderWidth: 1, borderColor: colors.line, borderRadius: radius.card, backgroundColor: colors.card },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm, flexShrink: 1 },
  spread: { justifyContent: "space-between", flexWrap: "wrap", rowGap: spacing.sm },
  label: { ...labelText, letterSpacing: 0.14 * typography.label.size.min, color: colors.textMuted },
  clear: { fontFamily: fontFamily.bodyStrong, fontSize: typography.bodySmall.size.min, color: colors.accent, textDecorationLine: "underline" },
});
