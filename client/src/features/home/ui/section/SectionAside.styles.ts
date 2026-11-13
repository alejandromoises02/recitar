import { StyleSheet } from "react-native";
import { colors } from "../../../../design/tokens";
import { labelText } from "../home.styles";

export const styles = StyleSheet.create({
  aside: { ...labelText, color: colors.textMuted },
});
