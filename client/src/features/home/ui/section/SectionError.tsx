import { Pressable, Text, View } from "react-native";
import { homeStrings } from "../strings";
import { styles } from "./SectionError.styles";

type Props = { onRetry: () => void; minHeight: number };

export function SectionError({ onRetry, minHeight }: Props) {
  return (
    <View style={[styles.error, { minHeight }]}>
      <Text style={styles.message}>{homeStrings.loadFailed}</Text>
      <Pressable accessibilityRole="button" onPress={onRetry} style={styles.retry} hitSlop={8}>
        <Text style={styles.retryText}>{homeStrings.retry}</Text>
      </Pressable>
    </View>
  );
}
