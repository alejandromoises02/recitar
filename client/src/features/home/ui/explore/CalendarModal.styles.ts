import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, scrim, spacing, typography } from "../../../../design/tokens";
import { labelText } from "../home.styles";
import { CALENDAR_CELL, CALENDAR_MAX_WIDTH, CLOSE_SIZE } from "./explore.constants";

export const styles = StyleSheet.create({
  backdrop: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.md, backgroundColor: scrim },
  dismiss: StyleSheet.absoluteFill,
  panel: {
    width: "100%",
    maxWidth: CALENDAR_MAX_WIDTH,
    gap: spacing.xs,
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
  monthRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: spacing.xs },
  month: { fontFamily: typography.headline.fontFamily, fontSize: 18, color: colors.text },
  arrow: { width: 36, height: 36, alignItems: "center", justifyContent: "center", borderRadius: radius.pill, borderWidth: 1, borderColor: colors.line },
  arrowOff: { opacity: 0.3 },
  arrowText: { fontFamily: fontFamily.bodyStrong, fontSize: 20, lineHeight: 22, color: colors.text },
  week: { flexDirection: "row", justifyContent: "space-between" },
  cell: { flex: 1, height: CALENDAR_CELL, alignItems: "center", justifyContent: "center" },
  weekday: { ...labelText, textAlign: "center", textAlignVertical: "center", lineHeight: CALENDAR_CELL, color: colors.textMuted },
  day: { borderRadius: radius.pill },
  today: { borderWidth: 1, borderColor: colors.accent },
  selected: { backgroundColor: colors.accent },
  dayText: { fontFamily: fontFamily.bodyStrong, fontSize: typography.body.size.min, color: colors.text },
  outside: { color: colors.textMuted },
  disabled: { opacity: 0.3 },
  selectedText: { color: colors.onAccent },
});
