import { StyleSheet } from "react-native";
import { colors, fontFamily, spacing, typography } from "../../../../design/tokens";
import { labelText } from "../home.styles";
import { BLOCK_GAP, CARD_GAP, GROUP_TITLE_SIZE } from "./explore.constants";

export const styles = StyleSheet.create({
  title: {
    marginTop: spacing.lg,
    fontFamily: fontFamily.displayMedium,
    fontSize: GROUP_TITLE_SIZE,
    letterSpacing: typography.headline.letterSpacing * GROUP_TITLE_SIZE,
    color: colors.text,
  },
  note: { color: colors.accent },
  count: { ...labelText, fontSize: 12, color: colors.textMuted },
  blocks: { flexDirection: "row", alignItems: "flex-start", gap: BLOCK_GAP },
  cards: { flexDirection: "row", alignItems: "stretch", gap: CARD_GAP },
});
