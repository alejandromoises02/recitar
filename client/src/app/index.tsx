import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/design/tokens";

export default function Home() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>recitAR</Text>
      <Text style={styles.subtitle}>Tu próximo show en Buenos Aires</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.background,
    gap: 8,
  },
  title: { color: colors.accent, fontSize: 40, fontWeight: "700" },
  subtitle: { color: colors.textMuted, fontSize: 16 },
});
