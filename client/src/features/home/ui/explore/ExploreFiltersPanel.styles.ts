import { StyleSheet } from "react-native";
import { colors, radius, spacing } from "../../../../design/tokens";

export const styles = StyleSheet.create({
  // Transparent around the panel so the page tint shows; no top padding, or rows would peek above it when pinned.
  backing: { paddingBottom: spacing.xs },
  // Opaque and rounded like the panel, so rows scrolling under the pinned panel do not show through it.
  underlay: { borderRadius: radius.card, backgroundColor: colors.background },
});
