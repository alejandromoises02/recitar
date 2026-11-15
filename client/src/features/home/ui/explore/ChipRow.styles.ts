import { StyleSheet } from "react-native";
import { spacing } from "../../../../design/tokens";
import { focusRoomContent, focusRoomScroll } from "../home.styles";

export const styles = StyleSheet.create({
  scroll: focusRoomScroll,
  row: { ...focusRoomContent, gap: spacing.xs },
});
