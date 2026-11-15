import { StyleSheet } from "react-native";
import { colors, fontFamily } from "../../../../design/tokens";
import { focusRoomContent, focusRoomScroll } from "../home.styles";
import { DAY_GAP, DAY_WIDTH } from "./explore.constants";

export const styles = StyleSheet.create({
  scroll: focusRoomScroll,
  row: { ...focusRoomContent, gap: DAY_GAP },
  day: { width: DAY_WIDTH, alignItems: "center", gap: 2, paddingVertical: 8, borderWidth: 1, borderColor: colors.line, borderRadius: 12 },
  more: { justifyContent: "center", minWidth: DAY_WIDTH, width: undefined, paddingHorizontal: 6, borderStyle: "dashed" },
  plus: { fontFamily: fontFamily.displayMedium, fontSize: 22, color: colors.accent },
  dayActive: { backgroundColor: colors.accent, borderColor: colors.accent },
  label: { fontFamily: fontFamily.bodyStrong, fontSize: 10.5, letterSpacing: 1, color: colors.textMuted },
  number: { fontFamily: fontFamily.displayMedium, fontSize: 18, color: colors.text },
  textActive: { color: colors.onAccent },
  dot: { width: 5, height: 5, borderRadius: 2.5, backgroundColor: colors.accent, opacity: 0 },
  dotOn: { opacity: 1 },
  dotActive: { backgroundColor: colors.onAccent },
});
