import { StyleSheet } from "react-native";
import { colors, spacing, typography } from "../../../../design/tokens";

const TITLE = typography.headline.size.min;

export const styles = StyleSheet.create({
  section: { paddingTop: spacing.lg },
  header: { flexDirection: "row", alignItems: "baseline", justifyContent: "space-between", gap: spacing.md },
  title: { fontFamily: typography.headline.fontFamily, fontSize: TITLE, letterSpacing: typography.headline.letterSpacing * TITLE, color: colors.text },
});
