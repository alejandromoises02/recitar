import { Pressable, Text } from "react-native";
import { styles } from "./Chip.styles";

type Props = { label: string; selected: boolean; onPress: () => void; accessibilityLabel?: string };

export function Chip({ label, selected, onPress, accessibilityLabel }: Props) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected }}
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      style={[styles.chip, selected && styles.selected]}
    >
      <Text style={[styles.text, selected && styles.selectedText]}>{label}</Text>
    </Pressable>
  );
}
