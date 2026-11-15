import { Pressable, Text, View } from "react-native";
import { SEGMENT_HEIGHT } from "./controls.constants";
import { verticalSlop } from "./hit-slop";
import { styles } from "./Segmented.styles";

const SEGMENT_SLOP = verticalSlop(SEGMENT_HEIGHT);

/** `accessibilityLabel`: what screen readers say when the visible label is an abbreviation. */
type Option<T extends string> = { value: T; label: string; accessibilityLabel?: string };
type Props<T extends string> = { options: Option<T>[]; value: T; onChange: (value: T) => void; accessibilityLabel: string };

export function Segmented<T extends string>({ options, value, onChange, accessibilityLabel }: Props<T>) {
  return (
    <View style={styles.track} role="radiogroup" aria-label={accessibilityLabel}>
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <Pressable
            key={option.value}
            role="radio"
            aria-checked={selected}
            aria-label={option.accessibilityLabel}
            onPress={() => onChange(option.value)}
            hitSlop={SEGMENT_SLOP}
            style={[styles.segment, selected && styles.selected]}
          >
            <Text style={[styles.text, selected && styles.selectedText]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}
