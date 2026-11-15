import { Pressable, Text, View } from "react-native";
import { useStrings } from "../strings";
import { styles } from "./ExploreEmpty.styles";

export function ExploreEmpty({ onClear }: { onClear: () => void }) {
  const strings = useStrings();
  return (
    <View style={styles.box}>
      <Text style={styles.message}>{strings.explore.empty}</Text>
      <Pressable accessibilityRole="button" onPress={onClear} style={styles.button}>
        <Text style={styles.buttonText}>{strings.explore.clear}</Text>
      </Pressable>
    </View>
  );
}
