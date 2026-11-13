import { StyleSheet } from "react-native";
import { colors } from "../../../../design/tokens";

export const styles = StyleSheet.create({
  track: { position: "absolute", left: 0, right: 0, bottom: 0, height: 3, backgroundColor: colors.line },
  fill: { height: "100%", backgroundColor: colors.accent, transformOrigin: "left" },
});
