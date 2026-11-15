import { StyleSheet } from "react-native";
import { colors, radius, spacing } from "../../../design/tokens";

export const styles = StyleSheet.create({
  layout: { flexDirection: "row", gap: spacing.xl, paddingTop: spacing.md },
  oneColumn: { flexDirection: "column", gap: spacing.lg },
  hidden: { position: "absolute", width: 1, height: 1, overflow: "hidden", opacity: 0 },
  block: { borderRadius: radius.cardSmall, backgroundColor: colors.surface },
  poster: { flex: 5, aspectRatio: 3 / 4 },
  posterOneColumn: { flex: 0, width: "100%", aspectRatio: 4 / 3 },
  info: { flex: 7, gap: spacing.md },
  name: { height: 56, width: "80%" },
  meta: { height: 20, width: "50%" },
  tiles: { height: 84, width: "70%" },
});
