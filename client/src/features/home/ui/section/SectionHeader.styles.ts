import { StyleSheet } from "react-native";
import { colors } from "../../../../design/tokens";
import { labelText } from "../home.styles";

export const styles = StyleSheet.create({
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", minHeight: 44 },
  title: { ...labelText, color: colors.textMuted },
});
