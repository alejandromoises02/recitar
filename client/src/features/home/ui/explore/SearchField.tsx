import { Text, TextInput, View } from "react-native";
import { colors } from "../../../../design/tokens";
import { useStrings } from "../strings";
import { styles } from "./SearchField.styles";

type Props = { value: string; onChange: (text: string) => void };

export function SearchField({ value, onChange }: Props) {
  const strings = useStrings();
  return (
    <View style={styles.field}>
      <Text style={styles.icon} aria-hidden>
        ⌕
      </Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder={strings.explore.searchPlaceholder}
        placeholderTextColor={colors.textMuted}
        accessibilityLabel={strings.explore.searchLabel}
        returnKeyType="search"
        autoCorrect={false}
        clearButtonMode="while-editing"
        style={styles.input}
      />
    </View>
  );
}
