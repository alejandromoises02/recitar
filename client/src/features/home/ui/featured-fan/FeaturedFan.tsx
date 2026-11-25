import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { LayoutChangeEvent } from "react-native";
import { useWindowSize } from "../../../../design/hydration";
import { AccessibilityInfo, View } from "react-native";
import { GestureDetector, useExclusiveGestures, usePanGesture, useTapGesture } from "react-native-gesture-handler";
import {
  cancelAnimation,
  useReducedMotion,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";
import { scheduleOnRN } from "react-native-worklets";
import { breakpoints, fan } from "../../../../design/tokens";
import { configuredApiBase } from "../../../events/infrastructure/events-api";
import { useFeatured } from "../../../events/infrastructure/events-queries";
import {
  fanCardSize,
  fanLanding,
  fanShift,
  fanSpread,
  tappedStep,
  tapsRecord,
} from "../../application/fan";
import { imageSource, spokenDate } from "../../application/show-labels";
import { SectionError } from "../section/SectionError";
import { SectionHeader } from "../section/SectionHeader";
import { useStrings } from "../strings";
import {
  DRAG_ACTIVATION,
  FAN_HEIGHT_SHARE,
  FAN_TOUCH_ACTION,
  RECORD_IN,
  RECORD_OUT,
  RECORD_OUT_DELAY,
  SLEEVE_MOVE,
  SPOT_WIDTH_SHARE,
} from "./featured.constants";
import { FanControls } from "./FanControls";
import { Pulse } from "../skeleton/Pulse";
import { styles } from "./FeaturedFan.styles";
import { Record } from "./Record";
import { Sleeve } from "./Sleeve";
import { SpotlightCard } from "./SpotlightCard";
import type { SampleHandle } from "./SpotifySample.types";
import { useFanAutoplay } from "./use-fan-autoplay";
import { edgeMask } from "./edge-mask";
import { useSetPageTint } from "../page-tint/page-tint-context";
import { useLang } from "../../../../i18n/lang-context";

const mod = (value: number, count: number) => ((value % count) + count) % count;

export function FeaturedFan() {
  const lang = useLang();
  const strings = useStrings();
  const { width: screen } = useWindowSize();
  const stacked = screen <= breakpoints.stacked;
  const card = fanCardSize(screen, stacked);
  const [apiBase] = useState(configuredApiBase);
  const { data, isPending, isError, refetch } = useFeatured();
  const shows = useMemo(() => data?.items ?? [], [data]);
  const count = shows.length;

  const reduced = useReducedMotion();
  const [current, setCurrent] = useState(0);
  const [recordOutFor, setRecordOutFor] = useState<number | null>(null);
  const [fanWidth, setFanWidth] = useState(0);
  const position = useSharedValue(0);
  const spread = useSharedValue(card / 2);
  const dragStart = useSharedValue(0);
  const recordShown = useSharedValue(0);
  const centreX = useSharedValue(0);
  const recordOut = recordOutFor === current;
  // Where the record is in the fan, for taps: x and y of its centre, its size, and whether it plays a sample.
  const recordHit = useSharedValue({ x: 0, y: 0, size: 0, playable: false });
  const sample = useRef<SampleHandle>(null);
  const [playing, setPlaying] = useState(false);

  const advance = useCallback(() => setCurrent((c) => c + 1), []);
  const { progress, active, stop, toggle } = useFanAutoplay(
    advance,
    count > 1,
    current,
  );

  useEffect(() => {
    position.set(reduced ? current : withTiming(current, SLEEVE_MOVE));
    const timer = setTimeout(
      () => setRecordOutFor(current),
      reduced ? 0 : RECORD_OUT_DELAY,
    );
    return () => clearTimeout(timer);
  }, [current, position, reduced]);

  useEffect(() => {
    const target = Number(recordOut);
    recordShown.set(
      reduced ? target : withTiming(target, recordOut ? RECORD_OUT : RECORD_IN),
    );
  }, [recordOut, recordShown, reduced]);

  // The carousel stops for good while a sample plays, as when the visitor touches it.
  const onPlaying = useCallback(
    (now: boolean) => {
      setPlaying(now);
      if (now) stop();
    },
    [stop],
  );

  const toggleSample = useCallback(() => {
    stop();
    sample.current?.toggle();
  }, [stop]);

  const userMove = useCallback(
    (target: number) => {
      stop();
      setCurrent(target);
      const show = shows[mod(target, count)];
      if (show)
        AccessibilityInfo.announceForAccessibility(
          `${show.name}, ${show.venue}, ${spokenDate(show.dates[0].startsAt, new Date(), lang)}`,
        );
    },
    [stop, count, shows, lang],
  );

  const selectStep = useCallback(
    (step: number) => userMove(current + step),
    [current, userMove],
  );

  const settleDrag = useCallback(
    (landing: number) => {
      if (landing !== current) {
        userMove(landing);
        return;
      }
      stop();
      position.set(withTiming(current, SLEEVE_MOVE));
      recordShown.set(withTiming(1, RECORD_OUT));
    },
    [current, position, recordShown, stop, userMove],
  );

  const pan = usePanGesture({
    activeOffsetX: [-DRAG_ACTIVATION, DRAG_ACTIVATION],
    failOffsetY: [-DRAG_ACTIVATION, DRAG_ACTIVATION],
    onActivate: () => {
      "worklet";
      // UI-thread only: a React update mid-drag reconfigures the gesture and drops the drag.
      dragStart.set(position.get());
      cancelAnimation(progress);
      recordShown.set(withTiming(0, RECORD_IN));
    },
    onUpdate: (event) => {
      "worklet";
      position.set(dragStart.get() - event.translationX / spread.get());
    },
    onDeactivate: (event) => {
      "worklet";
      scheduleOnRN(
        settleDrag,
        fanLanding(dragStart.get(), position.get(), event.velocityX),
      );
    },
  });

  const tap = useTapGesture({
    maxDistance: DRAG_ACTIVATION,
    onActivate: (event) => {
      "worklet";
      const record = recordHit.get();
      if (record.playable && recordShown.get() > 0.5 && tapsRecord(event.x, event.y, record.x, record.y, record.size)) {
        scheduleOnRN(toggleSample);
        return;
      }
      const step = tappedStep(event.x, centreX.get(), spread.get());
      if (step !== 0) scheduleOnRN(selectStep, step);
    },
  });
  const fanGesture = useExclusiveGestures(pan, tap);

  const onFanLayout = useCallback(
    (e: LayoutChangeEvent) => {
      setFanWidth(e.nativeEvent.layout.width);
      spread.set(fanSpread(e.nativeEvent.layout.width, card));
    },
    [card, spread],
  );

  const travel = card * (stacked ? fan.recordOutStacked : fan.recordOut);
  const recordSize = card * fan.recordSize;
  const shift = fanWidth > 0 ? fanShift(fanWidth, travel, recordSize) : 0;
  useEffect(() => centreX.set(fanWidth / 2 - shift), [centreX, fanWidth, shift]);

  const centre = count > 0 ? shows[mod(current, count)] : undefined;
  const playable = Boolean(centre?.spotifyArtistId);
  const centrePhoto = centre ? imageSource(centre.imageUrl, apiBase) : null;
  const setTint = useSetPageTint();
  useEffect(() => setTint(centrePhoto), [setTint, centrePhoto]);
  useEffect(() => () => setTint(null), [setTint]);
  useEffect(
    () => recordHit.set({ x: fanWidth / 2 - shift + travel, y: (card * FAN_HEIGHT_SHARE) / 2, size: recordSize, playable }),
    [recordHit, fanWidth, shift, travel, card, recordSize, playable],
  );

  if (!isPending && !isError && count === 0) return null;

  return (
    <View
      style={styles.section}
      role="region"
      aria-label={strings.featured.carousel}
    >
      <SectionHeader title={strings.sections.featured} />
      {isError ? (
        <SectionError onRetry={() => refetch()} minHeight={card} />
      ) : isPending ? (
        <View style={[styles.fan, styles.pending, { height: card * FAN_HEIGHT_SHARE }]}>
          <Pulse style={[styles.sleeveSkeleton, { width: card, height: card }]} />
        </View>
      ) : (
        <>
          <GestureDetector gesture={fanGesture} touchAction={FAN_TOUCH_ACTION}>
            <View
              style={[styles.fan, edgeMask, { height: card * FAN_HEIGHT_SHARE }]}
              onLayout={onFanLayout}
            >
              {/* Screen readers get the centre show from the spotlight card and move with the controls;
                  the sleeves would read every name out of order. */}
              <View
                style={[styles.stage, { transform: [{ translateX: -shift }] }]}
                aria-hidden
              >
                {shows.map((show, i) => (
                  <Sleeve
                    key={show.id}
                    show={show}
                    index={i}
                    count={count}
                    position={position}
                    spread={spread}
                    size={card}
                    apiBase={apiBase}
                  />
                ))}
                {centre ? (
                  <Record
                    size={recordSize}
                    travel={travel}
                    shown={recordShown}
                    photo={centrePhoto}
                    playable={playable}
                    playing={playing}
                  />
                ) : null}
              </View>
            </View>
          </GestureDetector>
          {count > 1 ? (
            <FanControls
              playing={active}
              onPrevious={() => userMove(current - 1)}
              onNext={() => userMove(current + 1)}
              onToggle={toggle}
            />
          ) : null}
          {centre && data ? (
            <SpotlightCard
              show={centre}
              kind={data.kind}
              width={card * SPOT_WIDTH_SHARE}
              progress={progress}
              showProgress={active}
              apiBase={apiBase}
              sampleRef={sample}
              onPlaying={onPlaying}
            />
          ) : null}
        </>
      )}
    </View>
  );
}
