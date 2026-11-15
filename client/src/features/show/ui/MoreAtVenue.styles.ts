import { StyleSheet } from "react-native";
import { colors, radius, spacing } from "../../../design/tokens";
import { surfacePanel } from "../../home/ui/home.styles";
import { CARD_GAP, CARD_IMAGE_RATIO } from "../../home/ui/explore/explore.constants";
import { sectionTitle } from "./show.styles";

export const styles = StyleSheet.create({
  section: { gap: spacing.md, paddingTop: spacing.xxl },
  title: sectionTitle,
  row: { flexDirection: "row", gap: CARD_GAP },
  // Shaped like an explore card with a one-line name, so the section keeps its height when the cards arrive.
  skeletonCard: { ...surfacePanel, borderRadius: radius.cardSmall, overflow: "hidden" },
  skeletonMedia: { aspectRatio: CARD_IMAGE_RATIO, backgroundColor: colors.surface },
  skeletonBody: { gap: spacing.hair, paddingHorizontal: 14, paddingTop: spacing.sm, paddingBottom: 14 },
  skeletonName: { width: "70%", height: 20, borderRadius: radius.flap, backgroundColor: colors.surface },
  skeletonPlace: { width: "45%", height: 16, borderRadius: radius.flap, backgroundColor: colors.surface },
});
