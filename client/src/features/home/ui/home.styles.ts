import type { TextStyle, ViewStyle } from "react-native";
import { colors, fontFamily, radius, spacing, typography } from "../../../design/tokens";

/** Style pieces shared by the home components; spread them into each component's styles. */

export const labelText: TextStyle = {
  fontFamily: typography.label.fontFamily,
  fontSize: typography.label.size.min,
  letterSpacing: typography.label.letterSpacing * typography.label.size.min,
  textTransform: "uppercase",
};

export const surfacePanel: ViewStyle = {
  borderWidth: 1,
  borderColor: colors.line,
  backgroundColor: colors.surface,
};

export const pillButton: ViewStyle = {
  paddingHorizontal: spacing.md,
  paddingVertical: spacing.xs,
  borderRadius: radius.pill,
  backgroundColor: colors.primary,
};

export const pillButtonText: TextStyle = {
  fontFamily: fontFamily.bodyStrong,
  fontSize: typography.bodySmall.size.min,
  color: colors.onPrimary,
};

export const mutedSmallText: TextStyle = {
  fontFamily: fontFamily.body,
  fontSize: typography.bodySmall.size.min,
  color: colors.textMuted,
};
