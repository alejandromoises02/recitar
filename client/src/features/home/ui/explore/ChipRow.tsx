import type { ReactNode } from "react";
import { ScrollView } from "react-native";
import { styles } from "./ChipRow.styles";

/** One line of chips that scrolls sideways when it does not fit: one choice (radiogroup) or several (group). */
export function ChipRow({ label, children, role = "radiogroup" }: { label: string; children: ReactNode; role?: "radiogroup" | "group" }) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.scroll} contentContainerStyle={styles.row} role={role} aria-label={label}>
      {children}
    </ScrollView>
  );
}
