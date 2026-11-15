import { StyleSheet } from "react-native";
import { colors, spacing } from "../../../design/tokens";
import { PAGE_MAX_WIDTH } from "./show.constants";

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { flexGrow: 1, width: "100%", maxWidth: PAGE_MAX_WIDTH, alignSelf: "center", paddingBottom: spacing.xxl },
});
