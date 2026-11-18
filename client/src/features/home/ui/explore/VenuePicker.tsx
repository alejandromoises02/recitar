import { useMemo, useState } from "react";
import { Modal, Pressable, ScrollView, Text, View } from "react-native";
import type { Venue } from "../../../events/domain/venue";
import { matchingVenues } from "../../application/venue-filter";
import { heading } from "../a11y";
import { useStrings } from "../strings";
import { SearchField } from "./SearchField";
import { styles } from "./VenuePicker.styles";

type Props = { venues: Venue[]; selected: string[]; onToggle: (venue: string) => void; onClose: () => void };

/**
 * Every venue, found by typing part of its name. Each row turns its venue on or off, so several can be picked
 * before "Listo"; Enter toggles the first match. Mounted only while open.
 */
export function VenuePicker({ venues, selected, onToggle, onClose }: Props) {
  const { venuePicker } = useStrings().explore;
  const [query, setQuery] = useState("");
  const found = useMemo(() => matchingVenues(venues, query), [venues, query]);

  return (
    <Modal visible transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        {/* Tapping outside closes too; the ✕ is the named, focusable way, so this one stays out of focus and screen readers. */}
        <Pressable style={styles.dismiss} onPress={onClose} accessible={false} focusable={false} importantForAccessibility="no" />
        <View style={styles.panel} accessibilityViewIsModal>
          <View style={styles.headingRow}>
            <Text style={styles.heading} {...heading(2)}>
              {venuePicker.title}
            </Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={venuePicker.close}
              onPress={onClose}
              style={({ pressed }) => [styles.close, pressed && styles.closePressed]}
              hitSlop={8}
            >
              <Text style={styles.closeText} aria-hidden>
                ✕
              </Text>
            </Pressable>
          </View>
          <SearchField
            value={query}
            onChange={setQuery}
            placeholder={venuePicker.searchPlaceholder}
            label={venuePicker.searchLabel}
            autoFocus
            onSubmit={() => found[0] && onToggle(found[0].name)}
          />
          <ScrollView style={styles.list} keyboardShouldPersistTaps="handled" role="group" aria-label={venuePicker.title}>
            {found.length === 0 ? (
              <Text style={styles.empty} role="status">
                {venuePicker.empty}
              </Text>
            ) : (
              found.map((venue) => {
                const chosen = selected.includes(venue.name);
                return (
                  <Pressable
                    key={venue.name}
                    role="checkbox"
                    aria-checked={chosen}
                    aria-label={`${venue.name}, ${venuePicker.dates(venue.upcomingEvents)}`}
                    onPress={() => onToggle(venue.name)}
                    style={({ pressed, hovered }: { pressed: boolean; hovered?: boolean }) => [
                      styles.row,
                      (pressed || hovered) && styles.rowActive,
                      chosen && styles.rowSelected,
                    ]}
                  >
                    <Text style={[styles.name, chosen && styles.nameSelected]} numberOfLines={1}>
                      {venue.name}
                    </Text>
                    <Text style={[styles.count, chosen && styles.countSelected]} aria-hidden>
                      {venuePicker.dates(venue.upcomingEvents)}
                    </Text>
                  </Pressable>
                );
              })
            )}
          </ScrollView>
          <Pressable
            accessibilityRole="button"
            onPress={onClose}
            style={({ pressed }) => [styles.done, pressed && styles.donePressed]}
          >
            <Text style={styles.doneText}>{venuePicker.done}</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}
