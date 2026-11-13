import { Pressable, Text, View } from "react-native";
import { styles } from "./Segmented.styles";

type Option<T extends string> = { value: T; label: string };
type Props<T extends string> = { options: Option<T>[]; value: T; onChange: (value: T) => void; accessibilityLabel: string };

export function Segmented<T extends string>({ options, value, onChange, accessibilityLabel }: Props<T>) {
  return (
    <View style={styles.track} accessibilityRole="radiogroup" accessibilityLabel={accessibilityLabel}>
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <Pressable
            key={option.value}
            accessibilityRole="radio"
            accessibilityState={{ selected }}
            onPress={() => onChange(option.value)}
            style={[styles.segment, selected && styles.selected]}
          >
            <Text style={[styles.text, selected && styles.selectedText]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}
