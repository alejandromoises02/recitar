import { StyleSheet } from "react-native";
import { colors, fontFamily, spacing, typography } from "../../../../design/tokens";
import { labelText } from "../home.styles";
import { GROUP_TITLE_SIZE, MIN_TARGET } from "./explore.constants";

export const styles = StyleSheet.create({
  wrap: { marginTop: spacing.lg },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm, minHeight: MIN_TARGET, alignSelf: "flex-start" },
  pressed: { opacity: 0.7 },
  chevron: { fontSize: GROUP_TITLE_SIZE, lineHeight: GROUP_TITLE_SIZE * 1.2, color: colors.accent },
  title: {
    flexShrink: 1,
    fontFamily: fontFamily.displayMedium,
    fontSize: GROUP_TITLE_SIZE,
    letterSpacing: typography.headline.letterSpacing * GROUP_TITLE_SIZE,
    color: colors.text,
  },
  note: { color: colors.accent },
  count: { ...labelText, fontSize: 12, color: colors.textMuted },
});
