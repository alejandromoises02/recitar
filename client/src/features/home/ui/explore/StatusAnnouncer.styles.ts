import { StyleSheet } from "react-native";

export const styles = StyleSheet.create({
  // Read by screen readers, never seen.
  hidden: { position: "absolute", width: 1, height: 1, overflow: "hidden", opacity: 0 },
});
