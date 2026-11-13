import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, typography } from "../../../../design/tokens";
import { labelText, mutedSmallText, surfacePanel } from "../home.styles";
import { THUMB_SIZE } from "./ShowCard.constants";

export const styles = StyleSheet.create({
  card: {
    ...surfacePanel,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    padding: spacing.xs,
    borderRadius: radius.cardSmall,
  },
  thumb: { width: THUMB_SIZE, height: THUMB_SIZE, borderRadius: radius.thumb },
  fallback: { alignItems: "center", justifyContent: "center", backgroundColor: colors.imageFallback },
  initials: { fontFamily: fontFamily.display, fontSize: 18, color: colors.text },
  text: { flex: 1, minWidth: 0, gap: 2 },
  when: { ...labelText, letterSpacing: 0.1 * typography.label.size.min, color: colors.accent },
  name: { fontFamily: fontFamily.bodyStrong, fontSize: typography.body.size.min, color: colors.text },
  place: mutedSmallText,
});
