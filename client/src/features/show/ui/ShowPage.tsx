import { Image } from "expo-image";
import * as Linking from "expo-linking";
import Head from "expo-router/head";
import { useState } from "react";
import { Platform, ScrollView, Text, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { spacing } from "../../../design/tokens";
import { useLang } from "../../../i18n/lang-context";
import type { Show } from "../../events/domain/show";
import { imageSource } from "../../home/application/show-labels";
import { domainOf } from "../../home/application/ticket-target";
import { heading } from "../../home/ui/a11y";
import { buttonWhen, dateTargets, updatedAgo } from "../application/show-page";
import { DateTiles } from "./DateTiles";
import { PinnedTicketBar } from "./PinnedTicketBar";
import { ShareButton } from "./ShareButton";
import { ONE_COLUMN_WIDTH, PINNED_BAR_HEIGHT, POSTER_MIN_RATIO_ONE_COLUMN } from "./show.constants";
import { ShowHeader } from "./ShowHeader";
import { nameSizing, styles } from "./ShowPage.styles";
import { ShowPoster } from "./ShowPoster";
import { useShowStrings } from "./strings";
import { TicketActions } from "./TicketActions";

type Props = { show: Show; apiBase: string };

/** The show page (design: .impeccable/surfaces/show-detail.md): pick a date, then one ticket button. */
export function ShowPage({ show, apiBase }: Props) {
  const strings = useShowStrings();
  const lang = useLang();
  const { width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const [now] = useState(() => new Date());
  const [picked, setPicked] = useState(0);

  const oneColumn = width <= ONE_COLUMN_WIDTH;
  const gutter = width < 600 ? spacing.md : spacing.xl;
  const date = show.dates[Math.min(picked, show.dates.length - 1)];
  const targets = dateTargets(date, show.sourceUrl);
  const when = buttonWhen(date.startsAt, now, lang);
  const photo = imageSource(show.imageUrl, apiBase);
  const several = show.dates.length > 1;
  const shareUrl = Platform.OS === "web" ? window.location.href : Linking.createURL(`/show/${show.id}`);

  return (
    <View style={styles.screen}>
      <Head>
        <title>{`${show.name} · recitAR`}</title>
      </Head>
      {photo ? (
        <View style={styles.tint} aria-hidden>
          <Image source={photo} style={styles.tintImage} blurRadius={60} contentFit="cover" />
          <View style={styles.tintFade} />
        </View>
      ) : null}
      <ScrollView
        contentContainerStyle={[
          styles.content,
          { paddingHorizontal: gutter, paddingTop: Platform.OS === "android" ? insets.top : 0, paddingBottom: oneColumn ? PINNED_BAR_HEIGHT + insets.bottom + spacing.lg : spacing.xxl },
        ]}
      >
        <ShowHeader compact={oneColumn} />
        <View role="main" style={[styles.layout, oneColumn && styles.oneColumn]}>
          <View style={oneColumn ? styles.posterOneColumn : styles.posterColumn}>
            <ShowPoster show={show} apiBase={apiBase} minRatio={oneColumn ? POSTER_MIN_RATIO_ONE_COLUMN : undefined} />
          </View>
          <View style={styles.info}>
            <View style={styles.titleRow}>
              <Text style={[styles.name, nameSizing(width)]} {...heading(1)}>
                {show.name}
              </Text>
              <ShareButton title={show.name} url={shareUrl} />
            </View>
            <Text style={styles.meta}>
              <Text style={styles.venue}>{show.venue}</Text>
              {" · "}
              <Text style={several ? styles.count : undefined}>{strings.dates(show.dates.length)}</Text>
              {` · ${strings.categories[show.category] ?? strings.categories.other}`}
            </Text>

            {several ? (
              <View style={styles.block}>
                <Text style={styles.h2} {...heading(2)}>
                  {strings.pickDate}
                </Text>
                <DateTiles dates={show.dates} picked={picked} onPick={setPicked} now={now} label={strings.pickDate} />
              </View>
            ) : (
              <Text style={styles.oneDate}>{when.replace(" · ", "  ")}</Text>
            )}

            <View style={styles.block}>
              {oneColumn && targets.length === 1 ? (
                <TicketActions targets={targets} when={when} showDomain onlyDomain />
              ) : (
                <TicketActions targets={targets} when={when} />
              )}
            </View>

            <Text style={styles.trust}>
              {strings.trust}
              {"\n"}
              {`${strings.dataFrom} `}
              <Text style={styles.strong}>{domainOf(show.sourceUrl)}</Text>
              {` · ${updatedAgo(show.updatedAt, now, lang)}`}
            </Text>
          </View>
        </View>
      </ScrollView>
      {oneColumn ? <PinnedTicketBar target={targets[0]} when={when} /> : null}
    </View>
  );
}
