import { StyleSheet } from "react-native";
import { colors, radius, spacing } from "../../../../design/tokens";
import { CARD_GAP, CARD_HEIGHT } from "./NextUpStrip.constants";

export const styles = StyleSheet.create({
  section: { gap: spacing.sm },
  arrows: { flexDirection: "row", gap: spacing.xs },
  row: { flexDirection: "row", gap: CARD_GAP, overflow: "hidden" },
  skeleton: { height: CARD_HEIGHT, borderRadius: radius.cardSmall, backgroundColor: colors.surface },
  separator: { width: CARD_GAP },
});
