import { router } from "expo-router";
import type { ReactNode } from "react";
import type { GestureResponderEvent, StyleProp, ViewStyle } from "react-native";
import { Platform, Pressable } from "react-native";
import { styles } from "./ShowLink.styles";

type Props = { showId: string; label?: string; style?: StyleProp<ViewStyle>; children: ReactNode };

// What a web click carries; React Native's press event type does not declare it.
type WebClick = { metaKey?: boolean; ctrlKey?: boolean; shiftKey?: boolean; button?: number; preventDefault?: () => void };

/**
 * Opens a show's page (/show/<id>). On web it is a real <a href>, so it can open in a new tab or be copied;
 * a plain click navigates inside the app. Not expo-router's <Link asChild>: it drops a Pressable's
 * function style, which broke the layout of every card.
 */
export function ShowLink({ showId, label, style, children }: Props) {
  const open = (event: GestureResponderEvent) => {
    if (Platform.OS === "web") {
      const click = event as unknown as WebClick;
      if (click.metaKey || click.ctrlKey || click.shiftKey || click.button === 1) return; // the browser opens a new tab
      click.preventDefault?.();
    }
    router.push({ pathname: "/show/[id]", params: { id: showId } });
  };
  return (
    <Pressable
      accessibilityRole="link"
      aria-label={label}
      {...(Platform.OS === "web" ? { href: `/show/${encodeURIComponent(showId)}` } : {})}
      onPress={open}
      style={({ pressed }) => [style, pressed && styles.pressed]}
    >
      {children}
    </Pressable>
  );
}
