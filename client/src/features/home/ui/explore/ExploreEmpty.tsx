import { Pressable, Text, View } from "react-native";
import { homeStrings } from "../strings";
import { styles } from "./ExploreEmpty.styles";

export function ExploreEmpty({ onClear }: { onClear: () => void }) {
  return (
    <View style={styles.box}>
      <Text style={styles.message}>{homeStrings.explore.empty}</Text>
      <Pressable accessibilityRole="button" onPress={onClear} style={styles.button}>
        <Text style={styles.buttonText}>{homeStrings.explore.clear}</Text>
      </Pressable>
    </View>
  );
}
