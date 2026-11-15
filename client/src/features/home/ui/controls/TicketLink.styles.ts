import { StyleSheet } from "react-native";
import { colors, fontFamily, motion, radius, spacing, touchTarget } from "../../../../design/tokens";
import { TICKET_ICON_SIZE } from "./controls.constants";

export const styles = StyleSheet.create({
  link: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    minHeight: touchTarget,
    paddingVertical: 6,
    paddingLeft: 6,
    paddingRight: 20,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
  },
  pressed: { transform: [{ scale: motion.scale.press }] },
  icon: { width: TICKET_ICON_SIZE, height: TICKET_ICON_SIZE, borderRadius: TICKET_ICON_SIZE / 2, alignItems: "center", justifyContent: "center", backgroundColor: colors.accent },
  iconText: { fontFamily: fontFamily.bodyStrong, fontSize: 16, color: colors.onAccent },
  texts: { flexShrink: 1 },
  label: { fontFamily: fontFamily.bodyStrong, fontSize: 14, color: colors.onPrimary },
  detail: { fontFamily: fontFamily.body, fontSize: 12.5, color: colors.onPrimary, opacity: 0.75 },
  // Read by screen readers, never seen; not display none, so it stays in the accessibility tree.
  hint: { position: "absolute", width: 1, height: 1, overflow: "hidden", opacity: 0 },
});
