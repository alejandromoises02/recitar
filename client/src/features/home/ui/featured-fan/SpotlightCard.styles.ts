import { StyleSheet } from "react-native";
import { colors, fontFamily, motion, radius, spacing, typography } from "../../../../design/tokens";
import { labelText, mutedSmallText } from "../home.styles";
import { CTA_ICON_SIZE } from "./featured.constants";

export const styles = StyleSheet.create({
  card: {
    alignSelf: "center",
    maxWidth: "100%",
    overflow: "hidden",
    padding: spacing.md,
    paddingBottom: spacing.md + 3,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.card,
    backgroundColor: colors.card,
  },
  top: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: spacing.sm, marginBottom: spacing.xs },
  tag: {
    ...labelText,
    letterSpacing: 0.08 * typography.label.size.min,
    paddingHorizontal: 10,
    paddingVertical: spacing.hair,
    borderRadius: radius.pill,
    overflow: "hidden",
    backgroundColor: colors.accent,
    color: colors.onAccent,
  },
  date: { ...labelText, fontSize: 12, letterSpacing: 0.12 * 12, fontVariant: ["tabular-nums"], color: colors.text },
  name: {
    fontFamily: typography.headline.fontFamily,
    fontSize: typography.headline.size.min,
    lineHeight: typography.headline.size.min * typography.headline.lineHeight,
    letterSpacing: typography.headline.letterSpacing * typography.headline.size.min,
    color: colors.text,
  },
  meta: { fontFamily: fontFamily.body, fontSize: typography.body.size.min, color: colors.textMuted, marginTop: 6, marginBottom: spacing.md },
  more: { fontFamily: fontFamily.bodyStrong, color: colors.accent },
  actions: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", columnGap: 18, rowGap: 10 },
  cta: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: 6,
    paddingLeft: 6,
    paddingRight: 20,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
  },
  ctaPressed: { transform: [{ scale: motion.scale.press }] },
  ctaIcon: { width: CTA_ICON_SIZE, height: CTA_ICON_SIZE, borderRadius: CTA_ICON_SIZE / 2, alignItems: "center", justifyContent: "center", backgroundColor: colors.accent },
  ctaIconText: { fontFamily: fontFamily.bodyStrong, fontSize: 16, color: colors.onAccent },
  ctaText: { fontFamily: fontFamily.bodyStrong, fontSize: 14, color: colors.onPrimary },
  source: { ...mutedSmallText, fontSize: 12.5 },
  sourceDomain: { fontFamily: fontFamily.bodyStrong, color: colors.text },
  trust: { ...mutedSmallText, fontSize: 12.5, marginTop: spacing.sm, paddingTop: spacing.sm, borderTopWidth: 1, borderTopColor: colors.line },
});
