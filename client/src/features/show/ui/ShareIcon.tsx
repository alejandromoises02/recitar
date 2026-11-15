import { View } from "react-native";
import { styles } from "./ShareIcon.styles";

/** The share mark drawn with borders (no icon library): an arrow rising out of an open tray. */
export function ShareIcon() {
  return (
    <View style={styles.box} aria-hidden>
      <View style={styles.tray} />
      <View style={styles.shaft} />
      <View style={styles.head} />
    </View>
  );
}
