import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, typography } from "../../../../design/tokens";
import { SEGMENT_HEIGHT } from "./controls.constants";

export const styles = StyleSheet.create({
  track: { flexDirection: "row", alignSelf: "flex-start", padding: 3, borderWidth: 1, borderColor: colors.line, borderRadius: radius.pill },
  segment: { height: SEGMENT_HEIGHT, justifyContent: "center", paddingHorizontal: 14, borderRadius: radius.pill },
  selected: { backgroundColor: colors.primary },
  text: { fontFamily: fontFamily.body, fontSize: typography.bodySmall.size.min, color: colors.textMuted },
  selectedText: { fontFamily: fontFamily.bodyStrong, color: colors.onPrimary },
});
