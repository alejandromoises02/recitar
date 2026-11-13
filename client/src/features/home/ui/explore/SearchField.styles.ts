import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, typography } from "../../../../design/tokens";
import { surfacePanel } from "../home.styles";

export const styles = StyleSheet.create({
  field: { ...surfacePanel, flexDirection: "row", alignItems: "center", gap: spacing.xs, height: 44, paddingHorizontal: 14, borderRadius: radius.pill },
  icon: { fontFamily: fontFamily.body, fontSize: 16, color: colors.textMuted },
  input: { flex: 1, height: "100%", fontFamily: fontFamily.body, fontSize: typography.body.size.min, color: colors.text },
});
