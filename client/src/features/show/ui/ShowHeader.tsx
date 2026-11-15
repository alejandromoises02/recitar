import { Link, router } from "expo-router";
import { Pressable, Text, View } from "react-native";
import { BrandLogo } from "../../home/ui/BrandLogo";
import { LangSwitch } from "../../home/ui/LangSwitch";
import { styles } from "./ShowHeader.styles";
import { useShowStrings } from "./strings";

/** Logo (home), the way back to the listing, and the language switch on web. */
export function ShowHeader({ compact }: { compact: boolean }) {
  const strings = useShowStrings();
  const back = () => (router.canGoBack() ? router.back() : router.replace("/"));
  return (
    <View style={styles.row}>
      <Link href="/">
        <BrandLogo size={compact ? 22 : 28} />
      </Link>
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
