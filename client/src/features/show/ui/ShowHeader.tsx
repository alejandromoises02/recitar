import { router } from "expo-router";
import type { GestureResponderEvent } from "react-native";
import { Platform, Pressable, Text, View } from "react-native";
import { BrandLogo } from "../../home/ui/BrandLogo";
import { LangSwitch } from "../../home/ui/LangSwitch";
import { styles } from "./ShowHeader.styles";
import { useShowStrings } from "./strings";

/** Logo (home), the way back to the listing, and the language switch on web. */
export function ShowHeader({ compact }: { compact: boolean }) {
  const strings = useShowStrings();
  const back = () => (router.canGoBack() ? router.back() : router.replace("/"));
  const goHome = (event: GestureResponderEvent) => {
    // On web a plain click stays in the app; with a modifier key the browser opens the link in a new tab.
    const click = event as unknown as { metaKey?: boolean; ctrlKey?: boolean; shiftKey?: boolean; button?: number; preventDefault?: () => void };
    if (Platform.OS === "web") {
      if (click.metaKey || click.ctrlKey || click.shiftKey || click.button === 1) return;
      click.preventDefault?.();
    }
    router.navigate("/");
  };
  return (
    <View style={styles.row}>
      {/* Not expo-router's <Link>: on iOS / Android it is a Text, whose line height clipped the top of the logo. */}
      <Pressable accessibilityRole="link" {...(Platform.OS === "web" ? { href: "/" } : {})} onPress={goHome}>
        <BrandLogo size={compact ? 22 : 28} />
      </Pressable>
      <Pressable accessibilityRole="button" accessibilityLabel={compact ? strings.backLabel : undefined} onPress={back} style={({ pressed }) => [styles.back, pressed && styles.pressed]}>
        <Text style={styles.chevron} aria-hidden>
          ‹
        </Text>
        {compact ? null : <Text style={styles.backText}>{strings.back}</Text>}
      </Pressable>
      <View style={styles.end}>
        <LangSwitch />
      </View>
    </View>
  );
}
