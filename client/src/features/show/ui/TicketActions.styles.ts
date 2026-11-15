import { StyleSheet } from "react-native";
import { colors, fontFamily, spacing } from "../../../design/tokens";

export const styles = StyleSheet.create({
  stack: { gap: spacing.sm },
  domain: { fontFamily: fontFamily.body, fontSize: 13, color: colors.textMuted },
});
