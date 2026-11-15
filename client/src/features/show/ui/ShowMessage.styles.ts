import { StyleSheet } from "react-native";
import { colors, fontFamily, spacing, typography } from "../../../design/tokens";
import { pillButton, pillButtonText } from "../../home/ui/home.styles";

export const styles = StyleSheet.create({
  box: { alignItems: "flex-start", gap: spacing.md, paddingVertical: spacing.xxl },
  title: { fontFamily: typography.headline.fontFamily, fontSize: 28, lineHeight: 32, color: colors.text },
  body: { fontFamily: fontFamily.body, fontSize: 15, color: colors.textMuted },
  button: pillButton,
  pressed: { opacity: 0.85 },
  buttonText: pillButtonText,
});
