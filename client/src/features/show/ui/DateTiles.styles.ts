import { StyleSheet } from "react-native";
import { colors, fontFamily, spacing } from "../../../design/tokens";
import { TILE_WIDTH } from "./show.constants";

export const styles = StyleSheet.create({
  row: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  tile: {
    width: TILE_WIDTH,
    alignItems: "center",
    gap: 1,
    paddingTop: 9,
    paddingBottom: 10,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 12,
    backgroundColor: colors.surface,
  },
  active: { backgroundColor: colors.accent, borderColor: colors.accent },
  small: { fontFamily: fontFamily.bodyStrong, fontSize: 10.5, letterSpacing: 1, color: colors.textMuted },
  day: { fontFamily: fontFamily.displayMedium, fontSize: 20, lineHeight: 24, color: colors.text },
  time: { fontFamily: fontFamily.body, fontSize: 11.5, color: colors.textMuted },
  activeText: { color: colors.onAccent },
});
