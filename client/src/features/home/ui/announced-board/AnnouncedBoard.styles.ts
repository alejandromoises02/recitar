import { StyleSheet } from "react-native";
import { spacing } from "../../../../design/tokens";
import { ROW_GAP } from "./board.constants";

export const styles = StyleSheet.create({
  section: { gap: spacing.xs },
  rows: { gap: ROW_GAP },
});
