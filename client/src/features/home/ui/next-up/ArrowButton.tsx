import { Pressable, Text } from "react-native";
import { styles } from "./ArrowButton.styles";

type Props = { label: string; glyph: string; onPress: () => void };

export function ArrowButton({ label, glyph, onPress }: Props) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      style={({ pressed }) => [styles.arrow, pressed && styles.pressed]}
    >
      <Text style={styles.glyph}>{glyph}</Text>
    </Pressable>
  );
}
