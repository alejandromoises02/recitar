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
  /** One choice among many (radio), one of several that can be on together (checkbox), or a button that opens something. */
  kind?: "radio" | "checkbox" | "action";
};

export function Chip({ label, selected, onPress, accessibilityLabel, kind = "radio" }: Props) {
  return (
    <Pressable
      role={kind === "action" ? "button" : kind}
      aria-checked={kind === "action" ? undefined : selected}
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      hitSlop={CHIP_SLOP}
      style={[styles.chip, selected && styles.selected]}
    >
      <Text style={[styles.text, selected && styles.selectedText]}>{label}</Text>
    </Pressable>
  );
}
