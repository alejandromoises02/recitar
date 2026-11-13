import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, typography } from "../../../../design/tokens";
import { mutedSmallText } from "../home.styles";
import { AGENDA_THUMB } from "./explore.constants";

export const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm, minHeight: AGENDA_THUMB + spacing.xs },
  thumb: { width: AGENDA_THUMB, height: AGENDA_THUMB, borderRadius: radius.thumb },
  fallback: { alignItems: "center", justifyContent: "center", backgroundColor: colors.imageFallback },
  initials: { fontFamily: fontFamily.display, fontSize: 16, color: colors.text },
  text: { flex: 1, minWidth: 0, gap: 2 },
  name: { fontFamily: fontFamily.bodyStrong, fontSize: typography.body.size.min, lineHeight: 19, color: colors.text },
  place: mutedSmallText,
  more: { fontFamily: fontFamily.bodyStrong, color: colors.accent },
});
