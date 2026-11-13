import { StyleSheet } from "react-native";
import { colors, radius, spacing } from "../../../design/tokens";
import { labelText, mutedSmallText, surfacePanel } from "./home.styles";

export const styles = StyleSheet.create({
  slot: { ...surfacePanel, borderStyle: "dashed", borderRadius: radius.card, padding: spacing.md, gap: spacing.xs },
  label: { ...labelText, color: colors.accent },
  status: mutedSmallText,
  error: { color: colors.text },
});
