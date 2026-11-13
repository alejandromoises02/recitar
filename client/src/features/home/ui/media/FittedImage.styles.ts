import { StyleSheet } from "react-native";
import { colors } from "../../../../design/tokens";
import { BACKDROP_DIM, BACKDROP_SCALE } from "./FittedImage.constants";

export const styles = StyleSheet.create({
  frame: { overflow: "hidden", backgroundColor: colors.imageFallback },
  backdrop: { ...StyleSheet.absoluteFill, transform: [{ scale: BACKDROP_SCALE }] },
  dim: { ...StyleSheet.absoluteFill, backgroundColor: colors.background, opacity: BACKDROP_DIM },
  image: StyleSheet.absoluteFill,
});
