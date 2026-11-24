import { StyleSheet } from "react-native";
import { colors, recordColors } from "../../../../design/tokens";
import { RECORD_BADGE_SHARE, RECORD_HOLE_SHARE, RECORD_LABEL_SHARE } from "./featured.constants";

const circle = (diameter: number) => ({ width: diameter, height: diameter, borderRadius: diameter / 2 });

export const recordGeometry = (size: number) => ({
  record: { ...circle(size), marginLeft: -size / 2, marginTop: -size / 2 },
  groove: (share: number) => circle(size * share),
  label: circle(size * RECORD_LABEL_SHARE),
  hole: circle(size * RECORD_HOLE_SHARE),
  badge: circle(size * RECORD_BADGE_SHARE),
  badgeGlyph: { fontSize: size * RECORD_BADGE_SHARE * 0.38 },
});

export const styles = StyleSheet.create({
  record: {
    position: "absolute",
    left: "50%",
    top: "50%",
    zIndex: 95,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: recordColors.vinyl,
    borderWidth: 2,
    borderColor: recordColors.rim,
    boxShadow: `0 18px 40px -10px ${recordColors.shadow}`,
  },
  disc: { ...StyleSheet.absoluteFill, alignItems: "center", justifyContent: "center" },
  groove: { position: "absolute", borderWidth: 1, borderColor: recordColors.groove },
  label: { alignItems: "center", justifyContent: "center", overflow: "hidden", backgroundColor: colors.imageFallback },
  labelImage: StyleSheet.absoluteFill,
  hole: { backgroundColor: colors.background },
  badge: { position: "absolute", alignItems: "center", justifyContent: "center", backgroundColor: colors.accent, boxShadow: `0 4px 12px ${recordColors.shadow}` },
  badgeGlyph: { color: colors.background, fontWeight: "700" },
});
