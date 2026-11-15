import { StyleSheet } from "react-native";
import { colors, spacing } from "../../../design/tokens";

export const styles = StyleSheet.create({
  bar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingTop: spacing.sm,
    paddingHorizontal: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.line,
    backgroundColor: colors.background,
  },
  link: { alignSelf: "stretch" },
});
