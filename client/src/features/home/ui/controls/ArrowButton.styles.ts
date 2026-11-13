import { StyleSheet } from "react-native";
import { colors, fontFamily, radius } from "../../../../design/tokens";
import { surfacePanel } from "../home.styles";

export const styles = StyleSheet.create({
  arrow: { ...surfacePanel, width: 44, height: 44, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
  pressed: { backgroundColor: colors.primary },
  glyph: { fontFamily: fontFamily.body, fontSize: 15, color: colors.text },
});
