import { StyleSheet } from "react-native";
import { colors, radius, spacing } from "../../../../design/tokens";
import { PHOTO_FADE_STOP } from "./board.constants";
import { hingeLine } from "./Flap.styles";

// Two fades, one per flap half, so the photo melts into each panel colour.
const fade = (color: string) => `linear-gradient(90deg, ${color}, transparent ${PHOTO_FADE_STOP})`;

export const styles = StyleSheet.create({
  strip: { position: "absolute", top: spacing.hair, right: spacing.hair, bottom: spacing.hair, borderRadius: radius.sleeve, overflow: "hidden" },
  image: StyleSheet.absoluteFill,
  fadeTop: { position: "absolute", left: 0, right: 0, top: 0, height: "50%", backgroundImage: fade(colors.flapTop) },
  fadeBottom: { position: "absolute", left: 0, right: 0, bottom: 0, height: "50%", backgroundImage: fade(colors.flapBottom) },
  hinge: hingeLine,
});
