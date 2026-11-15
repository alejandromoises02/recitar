import { Modal, Pressable, ScrollView, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useStrings } from "../strings";
import { BoundExploreFilters } from "./BoundExploreFilters";
import { styles } from "./FiltersSheet.styles";
import { heading } from "../a11y";

type Props = { visible: boolean; onClose: () => void };

/** Phones: every explore filter in a sheet from the bottom, opened from the compact filter bar. */
export function FiltersSheet({ visible, onClose }: Props) {
  const { explore } = useStrings();
  const insets = useSafeAreaInsets();
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        {/* Tapping above the sheet closes it; ✕ and "Listo" are the named, focusable ways. */}
        <Pressable style={styles.dismiss} onPress={onClose} accessible={false} focusable={false} importantForAccessibility="no" />
        <View style={[styles.sheet, { paddingBottom: insets.bottom + styles.sheet.padding }]} accessibilityViewIsModal>
          <View style={styles.headingRow}>
            <Text style={styles.heading} {...heading(2)}>
              {explore.filters}
            </Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={explore.calendar.close}
              onPress={onClose}
              style={({ pressed }) => [styles.close, pressed && styles.closePressed]}
              hitSlop={8}
            >
              <Text style={styles.closeText} aria-hidden>
                ✕
              </Text>
            </Pressable>
          </View>
          <ScrollView keyboardShouldPersistTaps="handled">
            <BoundExploreFilters />
          </ScrollView>
          <Pressable
            accessibilityRole="button"
            onPress={onClose}
            style={({ pressed }) => [styles.done, pressed && styles.donePressed]}
          >
            <Text style={styles.doneText}>{explore.filtersDone}</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}
