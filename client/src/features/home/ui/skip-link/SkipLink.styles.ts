import { StyleSheet } from "react-native";
import { pillButton, pillButtonText } from "../home.styles";

export const styles = StyleSheet.create({
  link: { ...pillButton, alignSelf: "flex-start" },
  // Visually hidden but still focusable and read by screen readers.
  hidden: { position: "absolute", width: 1, height: 1, padding: 0, overflow: "hidden", opacity: 0 },
  text: pillButtonText,
});
