import { StyleSheet } from "react-native";
import { colors, fontFamily, spacing } from "../../../design/tokens";

export const styles = StyleSheet.create({
  list: { alignSelf: "flex-start", minWidth: 260 },
  row: {
    flexDirection: "row",
    alignItems: "baseline",
    justifyContent: "space-between",
    gap: spacing.md,
    paddingVertical: spacing.xs,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
  },
  when: { fontFamily: fontFamily.board, fontSize: 20, letterSpacing: 1, textTransform: "uppercase", color: colors.text },
  soon: { fontFamily: fontFamily.bodyStrong, fontSize: 12, color: colors.textMuted },
});
