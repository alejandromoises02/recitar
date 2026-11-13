import { StyleSheet } from "react-native";
import { colors, spacing } from "../../../../design/tokens";
import { EDGE_FADE_SHARE } from "./featured.constants";

export const styles = StyleSheet.create({
  section: { gap: spacing.md },
  fan: { width: "100%", overflow: "hidden" },
  stage: StyleSheet.absoluteFill,
  edge: { position: "absolute", top: 0, bottom: 0, width: EDGE_FADE_SHARE, zIndex: 100 },
  edgeLeft: { left: 0, backgroundImage: `linear-gradient(90deg, ${colors.background}, transparent)` },
  edgeRight: { right: 0, backgroundImage: `linear-gradient(270deg, ${colors.background}, transparent)` },
});
