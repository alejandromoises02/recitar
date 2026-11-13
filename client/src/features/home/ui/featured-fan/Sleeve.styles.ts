import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, recordColors, spacing, typography } from "../../../../design/tokens";
import { SLEEVE_TITLE_SHARE, SLEEVE_VENUE_SHARE } from "./featured.constants";

export const sleeveText = (size: number) => {
  const title = size * SLEEVE_TITLE_SHARE;
  return {
    title: { fontFamily: fontFamily.display, fontSize: title, lineHeight: title * 1.05, letterSpacing: typography.headline.letterSpacing * title, color: colors.text },
    venue: { fontFamily: fontFamily.body, fontSize: size * SLEEVE_VENUE_SHARE, marginTop: spacing.xs, color: colors.textMuted },
  };
};

export const styles = StyleSheet.create({
  sleeve: {
    position: "absolute",
    left: "50%",
    top: "50%",
    borderRadius: radius.sleeve,
    backgroundColor: colors.imageFallback,
    transformOrigin: ["50%", "150%", 0],
    boxShadow: `0 30px 60px -22px ${recordColors.shadow}`,
  },
  fill: { width: "100%", height: "100%", borderRadius: radius.sleeve, overflow: "hidden" },
  // The fan's own tap and drag handle input; ignoring it here also stops the browser's image drag on web.
  content: { width: "100%", height: "100%", borderRadius: radius.sleeve, overflow: "hidden", pointerEvents: "none" },
  typeSleeve: { flex: 1, justifyContent: "flex-end", padding: "9%" },
  sheen: { ...StyleSheet.absoluteFill, backgroundImage: `linear-gradient(115deg, ${recordColors.sheen}, transparent 38%)` },
  shade: { ...StyleSheet.absoluteFill, backgroundColor: colors.background },
});
