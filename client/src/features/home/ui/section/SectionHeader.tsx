import type { ReactNode } from "react";
import { Text, View } from "react-native";
import { styles } from "./SectionHeader.styles";
import { heading } from "../a11y";

type Props = { title: string; children?: ReactNode };

export function SectionHeader({ title, children }: Props) {
  return (
    <View style={styles.header}>
      <Text style={styles.title} {...heading(2)}>
        {title}
      </Text>
      {children}
    </View>
  );
}
