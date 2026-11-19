import { Image } from "expo-image";
import * as Linking from "expo-linking";
import Head from "expo-router/head";
import { useEffect, useState } from "react";
import { Platform, ScrollView, Text, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { spacing } from "../../../design/tokens";
import { useLang } from "../../../i18n/lang-context";
import { tracker } from "../../analytics/tracker";
import type { ShowDetail } from "../../events/domain/show";
import { imageSource } from "../../home/application/show-labels";
import { domainOf } from "../../home/application/ticket-target";
import { heading } from "../../home/ui/a11y";
import { buttonWhen, dateMode, hasVenueToExplore, mapEmbedUrl, ticketPlan, updatedAgo, venueMapQuery } from "../application/show-page";
import { DateList } from "./DateList";
import { DateTiles } from "./DateTiles";
import { MoreAtVenue } from "./MoreAtVenue";
import { PinnedTicketBar } from "./PinnedTicketBar";
import { ShareButton } from "./ShareButton";
import { ONE_COLUMN_WIDTH, PINNED_BAR_HEIGHT, POSTER_MAX_HEIGHT_TWO_COLUMNS, POSTER_MIN_RATIO_ONE_COLUMN } from "./show.constants";
import { ShowHeader } from "./ShowHeader";
import { nameSizing, styles } from "./ShowPage.styles";
import { ShowPoster } from "./ShowPoster";
import { useShowStrings } from "./strings";
import { ticketOffer } from "./ticket-offer";
import { TicketActions } from "./TicketActions";
import { VenueMap } from "./VenueMap";

type Props = { show: ShowDetail; apiBase: string };

/** Beside the info the poster reaches at least the bottom of the info column ("Más en" included), and grows past the cap only to do so. */
const posterBesideInfo = (infoHeight: number) => ({ minHeight: infoHeight, maxHeight: Math.max(POSTER_MAX_HEIGHT_TWO_COLUMNS, infoHeight) });

/**
 * The show page (design: .impeccable/surfaces/show-detail.md). Dates are picked here only when each has
 * its own ticket page; when they share one (most ticketers) they are listed and the date is picked there.
 */
export function ShowPage({ show, apiBase }: Props) {
  const strings = useShowStrings();
  const lang = useLang();
  const { width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const [now] = useState(() => new Date());
  const [picked, setPicked] = useState(0);
  useEffect(() => tracker().showOpened(show.id, show.name, show.venue), [show.id, show.name, show.venue]);
  const [infoHeight, setInfoHeight] = useState(0);

  const oneColumn = width <= ONE_COLUMN_WIDTH;
  const gutter = width < 600 ? spacing.md : spacing.xl;
  const date = show.dates[Math.min(picked, show.dates.length - 1)];
  const mode = dateMode(show.dates);
  const when = buttonWhen(date.startsAt, now, lang, date.timeKnown);
  const offer = ticketOffer(ticketPlan(show.dates, picked, show.sourceUrl), when, strings, apiBase);
  const photo = imageSource(show.imageUrl, apiBase);
  const several = show.dates.length > 1;
  const mapQuery = venueMapQuery(show);
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
          { paddingHorizontal: gutter, paddingTop: insets.top, paddingBottom: oneColumn ? PINNED_BAR_HEIGHT + insets.bottom + spacing.lg : spacing.xxl },
        ]}
      >
        <ShowHeader compact={oneColumn} />
        <View role="main" style={[styles.layout, oneColumn && styles.oneColumn]}>
          <View style={oneColumn ? styles.posterOneColumn : styles.posterColumn}>
            <ShowPoster
              show={show}
              apiBase={apiBase}
              minRatio={oneColumn ? POSTER_MIN_RATIO_ONE_COLUMN : undefined}
              style={oneColumn ? undefined : posterBesideInfo(infoHeight)}
            />
          </View>
          <View style={[styles.info, oneColumn && styles.infoOneColumn]} onLayout={(event) => setInfoHeight(event.nativeEvent.layout.height)}>
            <View style={styles.titleRow}>
              <Text style={[styles.name, nameSizing(width)]} {...heading(1)}>
                {show.name}
              </Text>
              <ShareButton title={show.name} url={shareUrl} onShare={() => tracker().showShared(show.id, show.name, show.venue)} />
            </View>
            <Text style={styles.meta}>
              <Text style={styles.venue}>{show.venue}</Text>
              {" · "}
              <Text style={several ? styles.count : undefined}>{strings.dates(show.dates.length)}</Text>
              {` · ${strings.categories[show.category] ?? strings.categories.other}`}
            </Text>

            {mode === "pick" ? (
              <View style={styles.block}>
                <Text style={styles.h2} {...heading(2)}>
                  {strings.pickDate}
                </Text>
                <DateTiles dates={show.dates} picked={picked} onPick={setPicked} now={now} label={strings.pickDate} />
              </View>
            ) : mode === "list" ? (
              <View style={styles.block}>
                <Text style={styles.h2} {...heading(2)}>
                  {strings.datesTitle}
                </Text>
                <DateList dates={show.dates} now={now} />
              </View>
            ) : (
              <Text style={styles.oneDate}>{when.replace(" · ", "  ")}</Text>
            )}

            <View style={styles.block}>
              <TicketActions offer={offer} onlyNote={oneColumn && offer.links.length === 1} />
            </View>

            {oneColumn ? <View style={styles.trustGap} /> : null}
            <Text style={[styles.trust, oneColumn && styles.trustOneColumn]}>
              {strings.trust}
              {"\n"}
              {`${strings.dataFrom} `}
              <Text style={styles.strong}>{domainOf(show.sourceUrl)}</Text>
              {` · ${updatedAgo(show.updatedAt, now, lang)}`}
            </Text>
            {mapQuery ? (
              <View style={styles.block}>
                <Text style={styles.h2} {...heading(2)}>
                  {strings.whereTitle}
                </Text>
                <VenueMap url={mapEmbedUrl(mapQuery, lang)} label={strings.mapOf(show.venue)} />
              </View>
            ) : null}
            {oneColumn || !hasVenueToExplore(show.venue) ? null : <MoreAtVenue show={show} apiBase={apiBase} fillWidth />}
          </View>
        </View>
        {oneColumn && hasVenueToExplore(show.venue) ? <MoreAtVenue show={show} apiBase={apiBase} fillWidth={false} /> : null}
      </ScrollView>
      {oneColumn ? <PinnedTicketBar link={offer.links[0]} /> : null}
    </View>
  );
}
