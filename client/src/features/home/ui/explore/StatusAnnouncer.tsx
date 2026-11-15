import type { ComponentRef } from "react";
import { useEffect, useRef } from "react";
import { AccessibilityInfo, Platform, Text } from "react-native";
import { styles } from "./StatusAnnouncer.styles";

type Props = {
  /** What to say once the listing settles; null while it has nothing settled to say. */
  message: string | null;
  /** Changes when the user changes the filters: one announcement per change, none on first load or paging. */
  filtersKey: string;
  /** Errors are said even without a filter change (a retry that fails again). */
  urgent: boolean;
};

/** Says listing results without moving focus (WCAG 4.1.3): a polite live region on web, an announcement on iOS / Android. */
export function StatusAnnouncer({ message, filtersKey, urgent }: Props) {
  const lastKey = useRef(filtersKey);
  const lastMessage = useRef<string | null>(null);
  const region = useRef<ComponentRef<typeof Text>>(null);

  useEffect(() => {
    if (!message || message === lastMessage.current) return;
    if (filtersKey === lastKey.current && !urgent) return;
    lastKey.current = filtersKey;
    lastMessage.current = message;
    if (Platform.OS === "web") {
      const node = region.current as unknown as HTMLElement | null;
      if (node) node.textContent = message;
    } else {
      AccessibilityInfo.announceForAccessibility(message);
    }
  }, [message, filtersKey, urgent]);

  if (Platform.OS !== "web") return null;
  return <Text ref={region} aria-live="polite" style={styles.hidden} />;
}
