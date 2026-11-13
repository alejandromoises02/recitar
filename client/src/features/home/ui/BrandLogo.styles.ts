import { StyleSheet } from "react-native";
import { colors, fontFamily } from "../../../design/tokens";
import { LOGO_LINE_HEIGHT } from "./BrandLogo.constants";

export const logoText = (size: number) => ({ fontFamily: fontFamily.logo, fontSize: size, lineHeight: size * LOGO_LINE_HEIGHT });

export const styles = StyleSheet.create({
  layer: { position: "absolute", left: 0, top: 0 },
  face: { color: colors.accent },
});
