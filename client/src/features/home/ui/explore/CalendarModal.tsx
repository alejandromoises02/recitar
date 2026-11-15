import { useMemo, useState } from "react";
import { Modal, Pressable, Text, View } from "react-native";
import { monthGrid, monthTitle, shiftMonth } from "../../application/month-grid";
import { useStrings } from "../strings";
import { styles } from "./CalendarModal.styles";
import { useLang } from "../../../../i18n/lang-context";
import { spokenDate } from "../../application/show-labels";
import { heading } from "../a11y";

type Props = { visible: boolean; today: string; selected: string | null; onPick: (iso: string) => void; onClose: () => void };

/** A month calendar to pick any day from today on. */
export function CalendarModal({ visible, today, selected, onPick, onClose }: Props) {
  const lang = useLang();
  const { calendar } = useStrings().explore;
  const firstMonth = today.slice(0, 7);
  const [month, setMonth] = useState((selected ?? today).slice(0, 7));
  const weeks = useMemo(() => monthGrid(month, today), [month, today]);
  // Noon in Buenos Aires: any time of `today` works, spokenDate only needs its year.
  const todayDate = useMemo(() => new Date(`${today}T15:00:00Z`), [today]);
  const canGoBack = month > firstMonth;

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        {/* Tapping outside closes too; the ✕ is the named, focusable way, so this one stays out of focus and screen readers. */}
        <Pressable style={styles.dismiss} onPress={onClose} accessible={false} focusable={false} importantForAccessibility="no" />
        <View style={styles.panel} accessibilityViewIsModal>
          <View style={styles.headingRow}>
            <Text style={styles.heading} {...heading(2)}>
              {calendar.title}
            </Text>
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
              aria-disabled={!canGoBack}
              disabled={!canGoBack}
              onPress={() => setMonth(shiftMonth(month, -1))}
              style={[styles.arrow, !canGoBack && styles.arrowOff]}
              hitSlop={8}
            >
              <Text style={styles.arrowText}>‹</Text>
            </Pressable>
            <Text style={styles.month} {...heading(3)}>
              {monthTitle(month, lang)}
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
          <View style={styles.week} aria-hidden>
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
                    aria-disabled={cell.disabled}
                    aria-label={[spokenDate(cell.iso, todayDate, lang), cell.today && calendar.today, active && calendar.selected].filter(Boolean).join(", ")}
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
        </View>
      </View>
    </Modal>
  );
}
