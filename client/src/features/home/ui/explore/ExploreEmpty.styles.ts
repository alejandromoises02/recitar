import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, typography } from "../../../../design/tokens";
import { pillButton, pillButtonText } from "../home.styles";

export const styles = StyleSheet.create({
  box: { alignItems: "center", gap: 14, padding: 36, borderWidth: 1, borderStyle: "dashed", borderColor: colors.line, borderRadius: radius.card },
  message: { fontFamily: fontFamily.body, fontSize: typography.body.size.min, color: colors.text, textAlign: "center" },
  button: { ...pillButton, paddingVertical: spacing.sm },
  buttonText: pillButtonText,
});
