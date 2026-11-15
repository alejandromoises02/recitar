import { StyleSheet } from "react-native";
import { colors, spacing } from "../../../design/tokens";

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { flexGrow: 1, paddingBottom: spacing.xxl },
});
