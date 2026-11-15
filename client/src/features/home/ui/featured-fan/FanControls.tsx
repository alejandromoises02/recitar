import { Pressable, Text, View } from "react-native";
import { ArrowButton } from "../controls/ArrowButton";
import { useStrings } from "../strings";
import { styles } from "./FanControls.styles";

type Props = {
  playing: boolean;
  onPrevious: () => void;
  onNext: () => void;
  onToggle: () => void;
};

export function FanControls({ playing, onPrevious, onNext, onToggle }: Props) {
  const { featured } = useStrings();
  return (
    <View style={styles.controls}>
      <ArrowButton label={featured.previous} glyph="←" onPress={onPrevious} />
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ selected: !playing }}
        onPress={onToggle}
        style={({ pressed }) => [styles.toggle, pressed && styles.pressed]}
      >
        <Text style={styles.toggleIcon} aria-hidden>
          {playing ? "❚❚" : "▶"}
        </Text>
        <Text style={styles.toggleText}>
          {playing ? featured.pause : featured.play}
        </Text>
      </Pressable>
      <ArrowButton label={featured.next} glyph="→" onPress={onNext} />
    </View>
  );
}
