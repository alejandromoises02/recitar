import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing } from "../../../../design/tokens";
import { mutedSmallText, surfacePanel } from "../home.styles";
import { CARD_IMAGE_RATIO } from "./explore.constants";

export const styles = StyleSheet.create({
  // Fills its list item, which the row stretches to its tallest card, so every card in a row is as tall.
  card: { ...surfacePanel, flex: 1, borderRadius: radius.cardSmall, overflow: "hidden" },
  media: { aspectRatio: CARD_IMAGE_RATIO },
  image: StyleSheet.absoluteFill,
  fallback: { alignItems: "center", justifyContent: "center", backgroundColor: colors.imageFallback },
  initials: { fontFamily: fontFamily.display, fontSize: 34, color: colors.text },
  date: {
    position: "absolute",
    left: 10,
    top: 10,
    minWidth: 54,
    alignItems: "center",
    paddingVertical: 6,
    paddingHorizontal: spacing.xs,
    borderRadius: 10,
    backgroundColor: colors.badge,
  },
  dateSmall: { fontFamily: fontFamily.board, fontSize: 12, letterSpacing: 1, textTransform: "uppercase", color: colors.textMuted },
  dateDay: { fontFamily: fontFamily.board, fontSize: 26, lineHeight: 28, color: colors.accent },
  more: {
    position: "absolute",
    right: 10,
    top: 10,
    paddingHorizontal: 9,
    paddingVertical: spacing.hair,
    borderRadius: radius.pill,
    overflow: "hidden",
    backgroundColor: colors.accent,
    fontFamily: fontFamily.bodyStrong,
    fontSize: 11,
    color: colors.onAccent,
  },
  body: { gap: spacing.hair, paddingHorizontal: 14, paddingTop: spacing.sm, paddingBottom: 14 },
  name: { fontFamily: fontFamily.bodyStrong, fontSize: 16, lineHeight: 20, color: colors.text },
  place: mutedSmallText,
});
