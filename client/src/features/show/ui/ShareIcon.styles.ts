import { StyleSheet } from "react-native";
import { colors } from "../../../design/tokens";

const STROKE = 2;

export const styles = StyleSheet.create({
  box: { width: 18, height: 18 },
  tray: { position: "absolute", left: 1, right: 1, bottom: 0, height: 8, borderWidth: STROKE, borderTopWidth: 0, borderColor: colors.text, borderBottomLeftRadius: 2, borderBottomRightRadius: 2 },
  shaft: { position: "absolute", left: 8, top: 1, width: STROKE, height: 11, backgroundColor: colors.text },
  head: { position: "absolute", left: 5, top: 1, width: 8, height: 8, borderLeftWidth: STROKE, borderTopWidth: STROKE, borderColor: colors.text, transform: [{ rotate: "45deg" }] },
});
