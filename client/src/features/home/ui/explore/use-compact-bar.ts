import { useCallback, useState } from "react";
import type { LayoutChangeEvent } from "react-native";
import { useAnimatedScrollHandler, useSharedValue } from "react-native-reanimated";
import { scheduleOnRN } from "react-native-worklets";

/**
 * Phones: whether the explore filter panel has scrolled up past the top of the screen, so the compact
 * filter bar should take its place. `topInset` is the strip the status bar covers; `contentTop` is the
 * list's top padding above its header.
 */
export function useCompactBar(enabled: boolean, topInset: number, contentTop: number) {
  const [visible, setVisible] = useState(false);
  const headerHeight = useSharedValue(0);
  const panelHeight = useSharedValue(0);
  const past = useSharedValue(false);

  const onScroll = useAnimatedScrollHandler({
    onScroll: (event) => {
      const panelBottom = contentTop + headerHeight.get() + panelHeight.get();
      const now = enabled && panelHeight.get() > 0 && event.contentOffset.y + topInset >= panelBottom;
      if (now !== past.get()) {
        past.set(now);
        scheduleOnRN(setVisible, now);
      }
    },
  });

  const onHeaderLayout = useCallback((event: LayoutChangeEvent) => headerHeight.set(event.nativeEvent.layout.height), [headerHeight]);
  const onPanelLayout = useCallback((event: LayoutChangeEvent) => panelHeight.set(event.nativeEvent.layout.height), [panelHeight]);

  return { visible: enabled && visible, onScroll, onHeaderLayout, onPanelLayout };
}
