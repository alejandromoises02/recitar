import { Image } from "expo-image";
import { View } from "react-native";
import { styles } from "./PhotoStrip.styles";

type Props = { uri: string; share: number };

export function PhotoStrip({ uri, share }: Props) {
  return (
    <View style={[styles.strip, { width: `${share * 100}%` }]} pointerEvents="none">
      <Image source={uri} style={styles.image} contentFit="cover" contentPosition={{ top: "30%", left: "50%" }} transition={150} />
      <View style={styles.fadeTop} />
      <View style={styles.fadeBottom} />
      <View style={styles.hinge} />
    </View>
  );
}
