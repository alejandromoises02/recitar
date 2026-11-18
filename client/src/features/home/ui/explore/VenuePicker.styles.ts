import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, scrim, spacing, typography } from "../../../../design/tokens";
import { labelText, quietScrollbar } from "../home.styles";
import { CLOSE_SIZE, MIN_TARGET, VENUE_PICKER_MAX_HEIGHT, VENUE_PICKER_MAX_WIDTH } from "./explore.constants";

export const styles = StyleSheet.create({
  backdrop: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.md, backgroundColor: scrim },
  dismiss: StyleSheet.absoluteFill,
  panel: {
    width: "100%",
    maxWidth: VENUE_PICKER_MAX_WIDTH,
    maxHeight: VENUE_PICKER_MAX_HEIGHT,
    gap: spacing.sm,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.card,
    backgroundColor: colors.background,
  },
  headingRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  heading: { ...labelText, color: colors.textMuted },
  close: { width: CLOSE_SIZE, height: CLOSE_SIZE, alignItems: "center", justifyContent: "center", borderRadius: radius.pill, borderWidth: 1, borderColor: colors.line },
  closePressed: { backgroundColor: colors.surface },
  closeText: { fontFamily: fontFamily.bodyStrong, fontSize: 15, color: colors.text },
  list: { flexGrow: 0, ...quietScrollbar },
  row: {
    minHeight: MIN_TARGET,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.sm,
    paddingHorizontal: 14,
    borderRadius: radius.pill,
  },
  rowActive: { backgroundColor: colors.surface },
  rowSelected: { backgroundColor: colors.accent },
  name: { flexShrink: 1, fontFamily: fontFamily.body, fontSize: typography.body.size.min, color: colors.text },
  nameSelected: { fontFamily: fontFamily.bodyStrong, color: colors.onAccent },
  count: { fontFamily: fontFamily.body, fontSize: typography.bodySmall.size.min, color: colors.textMuted, fontVariant: ["tabular-nums"] },
  countSelected: { color: colors.onAccent },
  done: { minHeight: MIN_TARGET, alignItems: "center", justifyContent: "center", borderRadius: radius.pill, backgroundColor: colors.accent },
  donePressed: { opacity: 0.85 },
  doneText: { fontFamily: fontFamily.bodyStrong, fontSize: typography.body.size.min, color: colors.onAccent },
  empty: { paddingVertical: spacing.md, textAlign: "center", fontFamily: fontFamily.body, fontSize: typography.body.size.min, color: colors.textMuted },
});
