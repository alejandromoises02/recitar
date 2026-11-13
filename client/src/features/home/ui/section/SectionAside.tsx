import { Text } from "react-native";
import { styles } from "./SectionAside.styles";

/** Small text on the right of a section header, such as a count. */
export function SectionAside({ children }: { children: string }) {
  return <Text style={styles.aside}>{children}</Text>;
}
