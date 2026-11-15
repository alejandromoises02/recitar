import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, typography } from "../../../../design/tokens";
import { surfacePanel } from "../home.styles";

export const styles = StyleSheet.create({
  controls: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.xs },
  toggle: { ...surfacePanel, flexDirection: "row", alignItems: "center", gap: spacing.xs, minHeight: 44, paddingHorizontal: spacing.md, borderRadius: radius.pill },
  pressed: { backgroundColor: colors.primary },
  toggleIcon: { fontFamily: fontFamily.body, fontSize: typography.bodySmall.size.min, color: colors.text },
  toggleText: { fontFamily: fontFamily.bodyStrong, fontSize: typography.bodySmall.size.min, color: colors.text },
});
