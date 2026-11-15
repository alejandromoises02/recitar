import * as WebBrowser from "expo-web-browser";
import type { StyleProp, ViewStyle } from "react-native";
import { Platform, Pressable, Text, View } from "react-native";
import { styles } from "./TicketLink.styles";

type Props = {
  url: string;
  label: string;
  /** A second line under the label, e.g. the picked date. */
  detail?: string;
  /**
   * Web only, read after the visible text and never seen: the ticket domain and that a new tab opens. The
   * link is named by its content, so its name always starts with what is on screen (WCAG 2.5.3).
   */
  webHint: string;
  style?: StyleProp<ViewStyle>;
};

/** The way to tickets: a cream pill with the yellow arrow, the same everywhere a show can be bought. */
export function TicketLink({ url, label, detail, webHint, style }: Props) {
  return (
    <Pressable accessibilityRole="link" {...linkProps(url)} style={({ pressed }) => [styles.link, pressed && styles.pressed, style]}>
      <View style={styles.icon}>
        <Text style={styles.iconText} aria-hidden>
          ↗
        </Text>
      </View>
      <View style={styles.texts}>
        <Text style={styles.label}>{label}</Text>
        {detail ? <Text style={styles.detail}>{detail}</Text> : null}
        {Platform.OS === "web" ? <Text style={styles.hint}>{` ${webHint}`}</Text> : null}
      </View>
    </Pressable>
  );
}

/**
 * On web a real <a href> (react-native-web renders a View with href as a link): Enter, middle-click and
 * "open in new tab" work, and react-native-web would not run onPress from the keyboard for a link role.
 * On iOS / Android the in-app browser opens the ticket page.
 */
function linkProps(url: string): object {
  if (Platform.OS === "web") return { href: url, hrefAttrs: { target: "_blank", rel: "noopener noreferrer" } };
  return { onPress: () => WebBrowser.openBrowserAsync(url) };
}
