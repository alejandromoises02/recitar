import { memo } from "react";
import { Text, View } from "react-native";
import type { SharedValue } from "react-native-reanimated";
import Animated, { useAnimatedStyle } from "react-native-reanimated";
import type { Show } from "../../../events/domain/show";
import { fanOffset, fanPose } from "../../application/fan";
import { imageSource } from "../../application/show-labels";
import { FittedImage } from "../media/FittedImage";
import { sleeveText, styles } from "./Sleeve.styles";

type Props = {
  show: Show;
  index: number;
  count: number;
  position: SharedValue<number>;
  spread: SharedValue<number>;
  size: number;
  apiBase: string;
};

export const Sleeve = memo(function Sleeve({
  show,
  index,
  count,
  position,
  spread,
  size,
  apiBase,
}: Props) {
  const photo = imageSource(show.imageUrl, apiBase);
  const text = sleeveText(size);

  const pose = useAnimatedStyle(() => {
    const p = fanPose(fanOffset(index, position.get(), count), spread.get());
    return {
      zIndex: p.zIndex,
      opacity: p.visible ? 1 : 0,
      transform: [
        { translateX: p.translateX },
        { translateY: p.translateY },
        { rotate: `${p.rotate}deg` },
        { scale: p.scale },
      ],
    };
  });
  const shade = useAnimatedStyle(() => ({
    opacity: fanPose(fanOffset(index, position.get(), count), spread.get()).dim,
  }));

  return (
    <Animated.View
      style={[
        styles.sleeve,
        {
          width: size,
          height: size,
          marginLeft: -size / 2,
          marginTop: -size / 2,
        },
        pose,
      ]}
    >
      <View style={styles.content}>
        {photo ? (
          <FittedImage uri={photo} style={styles.fill} />
        ) : (
          <View style={styles.typeSleeve}>
            <Text style={text.title} numberOfLines={3}>
              {show.name}
            </Text>
            <Text style={text.venue} numberOfLines={1}>
              {show.venue}
            </Text>
          </View>
        )}
        <View style={styles.sheen} pointerEvents="none" />
        <Animated.View style={[styles.shade, shade]} pointerEvents="none" />
      </View>
    </Animated.View>
  );
});
