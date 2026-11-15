import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, scrim, spacing, typography } from "../../../../design/tokens";
import { CLOSE_SIZE, MIN_TARGET, SHEET_MAX_HEIGHT } from "./explore.constants";

export const styles = StyleSheet.create({
  backdrop: { flex: 1, justifyContent: "flex-end", backgroundColor: scrim },
  dismiss: { flex: 1 },
  sheet: {
    maxHeight: SHEET_MAX_HEIGHT,
    gap: spacing.sm,
    padding: spacing.md,
    borderTopLeftRadius: radius.card,
    borderTopRightRadius: radius.card,
    borderWidth: 1,
    borderBottomWidth: 0,
    borderColor: colors.line,
    backgroundColor: colors.background,
  },
  headingRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  heading: { fontFamily: typography.headline.fontFamily, fontSize: 18, color: colors.text },
  close: { width: CLOSE_SIZE, height: CLOSE_SIZE, alignItems: "center", justifyContent: "center", borderRadius: radius.pill, borderWidth: 1, borderColor: colors.line },
  closePressed: { backgroundColor: colors.surface },
  closeText: { fontFamily: fontFamily.bodyStrong, fontSize: 15, color: colors.text },
  done: { minHeight: MIN_TARGET, alignItems: "center", justifyContent: "center", borderRadius: radius.pill, backgroundColor: colors.accent },
  donePressed: { opacity: 0.85 },
  doneText: { fontFamily: fontFamily.bodyStrong, fontSize: typography.body.size.min, color: colors.onAccent },
});
