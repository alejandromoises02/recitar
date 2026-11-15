import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, typography } from "../../../../design/tokens";
import { CHIP_HEIGHT } from "./controls.constants";

export const styles = StyleSheet.create({
  chip: {
    minHeight: CHIP_HEIGHT,
    justifyContent: "center",
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.pill,
  },
  selected: { backgroundColor: colors.accent, borderColor: colors.accent },
  text: { fontFamily: fontFamily.body, fontSize: typography.bodySmall.size.min, color: colors.text },
  selectedText: { fontFamily: fontFamily.bodyStrong, color: colors.onAccent },
});
