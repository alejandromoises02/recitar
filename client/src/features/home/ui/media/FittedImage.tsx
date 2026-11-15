import { Image } from "expo-image";
import type { StyleProp, ViewStyle } from "react-native";
import { View } from "react-native";
import { BACKDROP_BLUR_RADIUS } from "./FittedImage.constants";
import { styles } from "./FittedImage.styles";

type Props = { uri: string; style?: StyleProp<ViewStyle> };

/** The whole image, never cropped, over a blurred copy of itself that fills the frame. Decorative: the show is named next to it. */
export function FittedImage({ uri, style }: Props) {
  return (
    <View style={[styles.frame, style]} aria-hidden>
      <Image source={uri} style={styles.backdrop} contentFit="cover" blurRadius={BACKDROP_BLUR_RADIUS} />
      <View style={styles.dim} />
      <Image source={uri} style={styles.image} contentFit="contain" transition={150} />
    </View>
  );
}
