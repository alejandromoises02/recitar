import type { ReactNode } from "react";
import { ScrollView } from "react-native";
import { styles } from "./ChipRow.styles";

/** One line of chips that scrolls sideways when it does not fit. */
export function ChipRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row} accessibilityLabel={label}>
      {children}
    </ScrollView>
  );
}
