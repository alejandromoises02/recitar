import { Pressable, Text, View } from "react-native";
import { useStrings } from "../strings";
import { styles } from "./SectionError.styles";

type Props = { onRetry: () => void; minHeight: number };

export function SectionError({ onRetry, minHeight }: Props) {
  const strings = useStrings();
  return (
    <View style={[styles.error, { minHeight }]}>
      <Text style={styles.message}>{strings.loadFailed}</Text>
      <Pressable accessibilityRole="button" onPress={onRetry} style={styles.retry} hitSlop={8}>
        <Text style={styles.retryText}>{strings.retry}</Text>
      </Pressable>
    </View>
  );
}
