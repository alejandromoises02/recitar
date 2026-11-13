import { StyleSheet } from "react-native";
import type { TextStyle } from "react-native";
import { colors, fontFamily, spacing, typography } from "../../../../design/tokens";
import { ROW_GAP } from "./board.constants";

const boardFace: TextStyle = { fontFamily: fontFamily.board, textTransform: "uppercase", fontVariant: ["tabular-nums"] };

/** The board face at `size`, with its letter spacing in points. */
export const boardText = (size: number): TextStyle => ({
  ...boardFace,
  fontSize: size,
  letterSpacing: typography.board.letterSpacing * size,
});

export const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: ROW_GAP },
  dateFlap: { alignItems: "center" },
  nameFlap: { flex: 1 },
  date: { color: colors.accent },
  name: { color: colors.text },
  nameBesidePhoto: { paddingRight: spacing.sm },
  sub: { ...boardFace, color: colors.textMuted, letterSpacing: 0.5 },
  more: { color: colors.accent },
});
