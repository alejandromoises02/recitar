import { StyleSheet } from "react-native";
import { colors, fontFamily, spacing, typography } from "../../../design/tokens";
import { BLOCK_GAP, CARD_GAP } from "./explore/explore.constants";
import { HEADLINE_LINE_HEIGHT } from "./HomeScreen.constants";

export const headlineSizing = (size: number) => ({
  fontSize: size,
  lineHeight: size * HEADLINE_LINE_HEIGHT,
  letterSpacing: typography.display.letterSpacing * size,
});

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { paddingBottom: spacing.xxxl },
  header: { gap: spacing.lg },
  rowGap: { height: BLOCK_GAP },
  cardRowGap: { height: CARD_GAP },
  headline: { fontFamily: typography.display.fontFamily, color: colors.text, maxWidth: 900 },
  city: { fontFamily: fontFamily.logo, color: colors.accent },
  hero: { flexDirection: "row", gap: spacing.xl, alignItems: "stretch" },
});
