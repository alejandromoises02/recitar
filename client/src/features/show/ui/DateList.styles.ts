import { StyleSheet } from "react-native";
import { colors, fontFamily, spacing } from "../../../design/tokens";
import { boardText } from "../../home/ui/announced-board/BoardRow.styles";

const LIST_MAX_WIDTH = 560;

export const styles = StyleSheet.create({
  list: { width: "100%", maxWidth: LIST_MAX_WIDTH, gap: spacing.xs },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md, minHeight: 44, paddingHorizontal: spacing.sm },
  date: { ...boardText(20), color: colors.accent, minWidth: 96 },
  time: { ...boardText(20), color: colors.text },
  until: { ...boardText(13), flex: 1, color: colors.textMuted },
  soon: { color: colors.accent },
  notOnSale: { fontFamily: fontFamily.bodyStrong, fontSize: 12, color: colors.textMuted },
});
