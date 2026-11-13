import { Text, TextInput, View } from "react-native";
import { colors } from "../../../../design/tokens";
import { homeStrings } from "../strings";
import { styles } from "./SearchField.styles";

type Props = { value: string; onChange: (text: string) => void };

export function SearchField({ value, onChange }: Props) {
  return (
    <View style={styles.field}>
      <Text style={styles.icon} aria-hidden>
        ⌕
      </Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder={homeStrings.explore.searchPlaceholder}
        placeholderTextColor={colors.textMuted}
        accessibilityLabel={homeStrings.explore.searchLabel}
        returnKeyType="search"
        autoCorrect={false}
        clearButtonMode="while-editing"
        style={styles.input}
      />
    </View>
  );
}
