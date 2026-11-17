import { Text, TextInput, View } from "react-native";
import { colors } from "../../../../design/tokens";
import { useStrings } from "../strings";
import { styles } from "./SearchField.styles";

type Props = {
  value: string;
  onChange: (text: string) => void;
  /** The listing's search by default; the venue picker gives its own. */
  placeholder?: string;
  label?: string;
  autoFocus?: boolean;
  onSubmit?: () => void;
};

export function SearchField({ value, onChange, placeholder, label, autoFocus, onSubmit }: Props) {
  const strings = useStrings();
  return (
    <View style={styles.field}>
      <Text style={styles.icon} aria-hidden>
        ⌕
      </Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder={placeholder ?? strings.explore.searchPlaceholder}
        placeholderTextColor={colors.textMuted}
        accessibilityLabel={label ?? strings.explore.searchLabel}
        autoFocus={autoFocus}
        onSubmitEditing={onSubmit}
        returnKeyType="search"
        autoCorrect={false}
        clearButtonMode="while-editing"
        style={styles.input}
      />
    </View>
  );
}
