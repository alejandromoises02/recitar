import { StyleSheet } from "react-native";
import { spacing } from "../../../../design/tokens";
import { mutedSmallText, pillButton, pillButtonText } from "../home.styles";

export const styles = StyleSheet.create({
  error: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  message: { ...mutedSmallText, flexShrink: 1 },
  retry: pillButton,
  retryText: pillButtonText,
});
