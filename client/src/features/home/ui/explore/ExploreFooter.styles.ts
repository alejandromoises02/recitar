import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, typography } from "../../../../design/tokens";
import { SKELETON_HEIGHT } from "./explore.constants";

export const styles = StyleSheet.create({
  skeletons: { gap: spacing.md },
  skeleton: { height: SKELETON_HEIGHT, borderRadius: radius.cardSmall, backgroundColor: colors.surface },
  loadingMore: {
    alignSelf: "center",
    paddingVertical: spacing.md,
    fontFamily: fontFamily.body,
    fontSize: typography.bodySmall.size.min,
    color: colors.textMuted,
  },
});
