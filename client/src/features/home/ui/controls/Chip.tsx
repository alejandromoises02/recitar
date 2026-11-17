import { Pressable, Text } from "react-native";
import { styles } from "./Chip.styles";
import { CHIP_HEIGHT } from "./controls.constants";
import { verticalSlop } from "./hit-slop";

const CHIP_SLOP = verticalSlop(CHIP_HEIGHT);

type Props = {
  label: string;
  selected: boolean;
  onPress: () => void;
  accessibilityLabel?: string;
  /** A chip that opens something instead of being one of the choices. */
  action?: boolean;
};

export function Chip({ label, selected, onPress, accessibilityLabel, action = false }: Props) {
  return (
    <Pressable
      role={action ? "button" : "radio"}
      aria-checked={action ? undefined : selected}
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      hitSlop={CHIP_SLOP}
      style={[styles.chip, selected && styles.selected]}
    >
      <Text style={[styles.text, selected && styles.selectedText]}>{label}</Text>
    </Pressable>
  );
}
