import { StyleSheet } from "react-native";
import { colors, fontFamily, spacing, typography } from "../../../design/tokens";
import { NAME_MAX_SIZE, NAME_MIN_SIZE, TINT_HEIGHT } from "./show.constants";

/** The name scales with the screen and shrinks on phones so a long single word still fits. */
export const nameSizing = (width: number) => {
  const size = Math.round(Math.min(NAME_MAX_SIZE, Math.max(NAME_MIN_SIZE, width * 0.05)));
  return { fontSize: size, lineHeight: size * 1.02, letterSpacing: typography.display.letterSpacing * size };
};

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  tint: { position: "absolute", top: 0, left: 0, right: 0, height: TINT_HEIGHT },
  tintImage: { ...StyleSheet.absoluteFill, opacity: 0.22 },
  // The tint fades into the page instead of ending in a hard line.
  tintFade: { ...StyleSheet.absoluteFill, backgroundImage: `linear-gradient(to bottom, transparent 35%, ${colors.background})` },
  content: { flexGrow: 1 },
  layout: { flexDirection: "row", alignItems: "flex-start", gap: spacing.xxl, paddingTop: spacing.md },
  oneColumn: { flexDirection: "column", gap: spacing.lg },
  posterColumn: { flex: 5 },
  posterOneColumn: { width: "100%" },
  info: { flex: 7, alignSelf: "stretch" },
  titleRow: { flexDirection: "row", alignItems: "flex-start", gap: spacing.md },
  name: { flex: 1, fontFamily: typography.display.fontFamily, color: colors.text },
  meta: { marginTop: spacing.sm, fontFamily: fontFamily.body, fontSize: 16, color: colors.textMuted },
  venue: { fontFamily: fontFamily.bodyStrong, color: colors.text },
  count: { fontFamily: fontFamily.bodyStrong, color: colors.accent },
  block: { marginTop: spacing.lg, gap: spacing.sm },
  h2: { fontFamily: typography.headline.fontFamily, fontSize: 18, color: colors.text },
  oneDate: { marginTop: spacing.lg, fontFamily: fontFamily.board, fontSize: 28, letterSpacing: 1.5, textTransform: "uppercase", color: colors.accent },
  trust: {
    marginTop: spacing.xl,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.line,
    fontFamily: fontFamily.body,
    fontSize: 13,
    lineHeight: 20,
    color: colors.textMuted,
    maxWidth: 560,
  },
  strong: { fontFamily: fontFamily.bodyStrong, color: colors.text },
});
