import { StyleSheet } from "react-native";
import { colors, spacing } from "../../../../design/tokens";

export const styles = StyleSheet.create({
  // Opaque, so rows scrolling under the pinned panel do not show through it.
  backing: { paddingVertical: spacing.xs, backgroundColor: colors.background },
});
