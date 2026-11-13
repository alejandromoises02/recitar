import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing } from "../../../../design/tokens";
import { surfacePanel } from "../home.styles";
import { DATE_COLUMN_WIDTH } from "./explore.constants";

export const styles = StyleSheet.create({
  block: { ...surfacePanel, flexDirection: "row", gap: spacing.sm, padding: spacing.xs, borderRadius: radius.cardSmall },
  date: { width: DATE_COLUMN_WIDTH, alignItems: "center", paddingVertical: spacing.xs, borderRadius: 10, backgroundColor: colors.card },
  small: { fontFamily: fontFamily.board, fontSize: 12, letterSpacing: 1, textTransform: "uppercase", color: colors.textMuted },
  day: { fontFamily: fontFamily.board, fontSize: 26, lineHeight: 28, color: colors.accent },
  note: { marginTop: spacing.hair, fontFamily: fontFamily.bodyStrong, fontSize: 10, letterSpacing: 0.8, textTransform: "uppercase", color: colors.text },
  rows: { flex: 1, minWidth: 0, gap: spacing.xs },
});
