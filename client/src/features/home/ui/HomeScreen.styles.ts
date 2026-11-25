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
  root: { flex: 1, backgroundColor: colors.background },
  screen: { flex: 1 },
  content: { paddingBottom: spacing.xxxl },
  header: { gap: spacing.lg },
  topRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.md },
  rowGap: { height: BLOCK_GAP },
  cardRowGap: { height: CARD_GAP },
  headline: { fontFamily: typography.display.fontFamily, color: colors.text, maxWidth: 900 },
  city: { fontFamily: fontFamily.logo, color: colors.accent },
  compactBar: { position: "absolute", left: 0, right: 0 },
  hero: { flexDirection: "row", gap: spacing.xl, alignItems: "stretch" },
});
