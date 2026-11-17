import { Platform, type TextStyle, type ViewStyle } from "react-native";
import { colors, focusRing, fontFamily, radius, spacing, touchTarget, typography } from "../../../design/tokens";

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
  minHeight: touchTarget,
  justifyContent: "center",
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

/** Sideways scroll rows clip what overflows: leave room for the focus ring and pull the row back so nothing shifts. */
export const focusRoomScroll: ViewStyle = { margin: -focusRing.room };
export const focusRoomContent: ViewStyle = { padding: focusRing.room };

/**
 * A thin scrollbar in the palette instead of the browser's white one (web only; native shows its own
 * indicator). React Native's types lack these CSS properties, which react-native-web passes through.
 */
export const quietScrollbar: ViewStyle =
  Platform.OS === "web" ? ({ scrollbarWidth: "thin", scrollbarColor: `${colors.fieldBorder} transparent` } as ViewStyle) : {};
