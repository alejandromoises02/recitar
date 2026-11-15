import { useState } from "react";
import { Platform, Pressable, Text } from "react-native";
import { useStrings } from "../strings";
import { EXPLORE_ANCHOR } from "./skip-link.constants";
import { styles } from "./SkipLink.styles";

/** Web only: the first stop for the keyboard, hidden until focused, jumps past the hero to the listing. */
export function SkipLink() {
  const strings = useStrings();
  const [focused, setFocused] = useState(false);
  if (Platform.OS !== "web") return null;
  return (
    <Pressable
      // A button, not a link: react-native-web runs onPress from the keyboard only for buttons (a link without href does nothing).
      role="button"
      onPress={() => document.getElementById(EXPLORE_ANCHOR)?.focus()}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={[styles.link, !focused && styles.hidden]}
    >
      <Text style={styles.text}>{strings.skipToListing}</Text>
    </Pressable>
  );
}
