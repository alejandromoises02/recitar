import { StyleSheet } from "react-native";
import { colors, radius, spacing } from "../../../../design/tokens";

export const styles = StyleSheet.create({
  section: { gap: spacing.md },
  fan: { width: "100%", overflow: "hidden" },
  pending: { alignItems: "center", justifyContent: "center" },
  sleeveSkeleton: { borderRadius: radius.sleeve, backgroundColor: colors.surface },
  stage: StyleSheet.absoluteFill,
});
