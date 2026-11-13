import { useMemo, useState } from "react";
import { Modal, Pressable, Text, View } from "react-native";
import { monthGrid, monthTitle, shiftMonth } from "../../application/month-grid";
import { homeStrings } from "../strings";
import { styles } from "./CalendarModal.styles";

type Props = { visible: boolean; today: string; selected: string | null; onPick: (iso: string) => void; onClose: () => void };

/** A month calendar to pick any day from today on. */
export function CalendarModal({ visible, today, selected, onPick, onClose }: Props) {
  const { calendar } = homeStrings.explore;
  const firstMonth = today.slice(0, 7);
  const [month, setMonth] = useState((selected ?? today).slice(0, 7));
  const weeks = useMemo(() => monthGrid(month, today), [month, today]);
  const canGoBack = month > firstMonth;

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose} accessibilityLabel={calendar.close}>
        <Pressable style={styles.panel} onPress={() => undefined} accessibilityViewIsModal>
          <View style={styles.headingRow}>
            <Text style={styles.heading}>{calendar.title}</Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={calendar.close}
              onPress={onClose}
              style={({ pressed }) => [styles.close, pressed && styles.closePressed]}
              hitSlop={8}
            >
              <Text style={styles.closeText} aria-hidden>
                ✕
              </Text>
            </Pressable>
          </View>
          <View style={styles.monthRow}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={calendar.previous}
              accessibilityState={{ disabled: !canGoBack }}
              disabled={!canGoBack}
              onPress={() => setMonth(shiftMonth(month, -1))}
              style={[styles.arrow, !canGoBack && styles.arrowOff]}
              hitSlop={8}
            >
              <Text style={styles.arrowText}>‹</Text>
            </Pressable>
            <Text style={styles.month} accessibilityRole="header">
              {monthTitle(month)}
            </Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={calendar.next}
              onPress={() => setMonth(shiftMonth(month, 1))}
              style={styles.arrow}
              hitSlop={8}
            >
              <Text style={styles.arrowText}>›</Text>
            </Pressable>
          </View>
          <View style={styles.week}>
            {calendar.weekdays.map((letter, i) => (
              <Text key={i} style={[styles.cell, styles.weekday]}>
                {letter}
              </Text>
            ))}
          </View>
          {weeks.map((week) => (
            <View key={week[0].iso} style={styles.week}>
              {week.map((cell) => {
                const active = cell.iso === selected;
                return (
                  <Pressable
                    key={cell.iso}
                    accessibilityRole="button"
                    accessibilityState={{ disabled: cell.disabled, selected: active }}
                    disabled={cell.disabled}
                    onPress={() => onPick(cell.iso)}
                    style={[styles.cell, styles.day, cell.today && styles.today, active && styles.selected]}
                  >
                    <Text
                      style={[
                        styles.dayText,
                        !cell.inMonth && styles.outside,
                        cell.disabled && styles.disabled,
                        active && styles.selectedText,
                      ]}
                    >
                      {cell.day}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          ))}
        </Pressable>
      </Pressable>
    </Modal>
  );
}
