import { Pressable, Text } from "react-native";
import { styles } from "./Chip.styles";
import { CHIP_HEIGHT } from "./controls.constants";
import { verticalSlop } from "./hit-slop";

const CHIP_SLOP = verticalSlop(CHIP_HEIGHT);

type Props = { label: string; selected: boolean; onPress: () => void; accessibilityLabel?: string };

export function Chip({ label, selected, onPress, accessibilityLabel }: Props) {
  return (
    <Pressable
      role="radio"
      aria-checked={selected}
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      hitSlop={CHIP_SLOP}
      style={[styles.chip, selected && styles.selected]}
    >
      <Text style={[styles.text, selected && styles.selectedText]}>{label}</Text>
    </Pressable>
  );
}
