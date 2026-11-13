import { StyleSheet } from "react-native";
import { colors, recordColors } from "../../../../design/tokens";
import { RECORD_HOLE_SHARE, RECORD_LABEL_SHARE } from "./featured.constants";

const circle = (diameter: number) => ({ width: diameter, height: diameter, borderRadius: diameter / 2 });

export const recordGeometry = (size: number) => ({
  record: { ...circle(size), marginLeft: -size / 2, marginTop: -size / 2 },
  groove: (share: number) => circle(size * share),
  label: circle(size * RECORD_LABEL_SHARE),
  hole: circle(size * RECORD_HOLE_SHARE),
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
  groove: { position: "absolute", borderWidth: 1, borderColor: recordColors.groove },
  label: { alignItems: "center", justifyContent: "center", overflow: "hidden", backgroundColor: colors.imageFallback },
  labelImage: StyleSheet.absoluteFill,
  hole: { backgroundColor: colors.background },
});
