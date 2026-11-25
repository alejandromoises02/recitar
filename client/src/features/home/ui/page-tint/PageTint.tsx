import { Image } from "expo-image";
import { View } from "react-native";
import { useReducedMotion } from "react-native-reanimated";
import { usePageTint } from "./page-tint-context";
import { TINT_BLUR_RADIUS, TINT_CROSSFADE_MS } from "./PageTint.constants";
import { styles } from "./PageTint.styles";

/**
 * A heavily blurred copy of the featured show's image fixed behind the whole home, so the page
 * takes the colour of the record in the spotlight while the content scrolls over it. Decorative.
 */
export function PageTint() {
  const uri = usePageTint();
  const reduced = useReducedMotion();
  if (!uri) return null;
  return (
    <View style={styles.tint} aria-hidden pointerEvents="none">
      <Image
        source={uri}
        style={styles.image}
        contentFit="cover"
        blurRadius={TINT_BLUR_RADIUS}
        transition={reduced ? 0 : { duration: TINT_CROSSFADE_MS, effect: "cross-dissolve" }}
      />
      <View style={styles.vignette} />
    </View>
  );
}
