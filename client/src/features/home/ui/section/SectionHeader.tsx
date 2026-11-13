import type { ReactNode } from "react";
import { Text, View } from "react-native";
import { styles } from "./SectionHeader.styles";

type Props = { title: string; children?: ReactNode };

export function SectionHeader({ title, children }: Props) {
  return (
    <View style={styles.header}>
      <Text style={styles.title} accessibilityRole="header">
        {title}
      </Text>
      {children}
    </View>
  );
}
