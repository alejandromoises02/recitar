import { useEffect } from "react";
import { Pressable, Text, View } from "react-native";
import Animated, { useAnimatedStyle, useReducedMotion, useSharedValue, withTiming } from "react-native-reanimated";
import { useStrings } from "../strings";
import { CHEVRON_TURN } from "./explore.constants";
import { useExploreContext } from "./explore-context";
import { styles } from "./GroupTitle.styles";
import { heading } from "../a11y";

type Props = { group: string; title: string; note: string | null; count: number; expanded: boolean };

/** A listing group's title: tapping it folds or unfolds the group's shows. */
export function GroupTitle({ group, title, note, count, expanded }: Props) {
  const strings = useStrings();
  const { toggleGroup } = useExploreContext();
  const reduced = useReducedMotion();
  const turn = useSharedValue(expanded ? 0 : CHEVRON_TURN.collapsed);

  useEffect(() => {
    const target = expanded ? 0 : CHEVRON_TURN.collapsed;
    turn.set(reduced ? target : withTiming(target, CHEVRON_TURN.timing));
  }, [expanded, reduced, turn]);

  const chevron = useAnimatedStyle(() => ({ transform: [{ rotate: `${turn.get()}deg` }] }));
  const shows = strings.shows(count, false);

  return (
    <View {...heading(3)} style={styles.wrap}>
      <Pressable
        onPress={() => toggleGroup(group)}
        accessibilityRole="button"
        aria-expanded={expanded}
        accessibilityLabel={strings.explore.groupLabel(title, note, shows)}
        style={({ pressed }) => [styles.row, pressed && styles.pressed]}
      >
        <Animated.Text style={[styles.chevron, chevron]}>▾</Animated.Text>
        <Text style={styles.title}>
          {title}
          {note ? <Text style={styles.note}>{` · ${note}`}</Text> : null}
          <Text style={styles.count}>{`  ${shows}`}</Text>
        </Text>
      </Pressable>
    </View>
  );
}
