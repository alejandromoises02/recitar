import { useState } from "react";
import { View, useWindowDimensions } from "react-native";
import { fluid } from "../../../../design/fluid";
import { breakpoints, typography } from "../../../../design/tokens";
import { announcedFrom } from "../../../events/application/announced-from";
import { configuredApiBase } from "../../../events/infrastructure/events-api";
import { useShows } from "../../../events/infrastructure/events-queries";
import { ANNOUNCED_COUNT } from "../home.constants";
import { SectionAside } from "../section/SectionAside";
import { SectionError } from "../section/SectionError";
import { SectionHeader } from "../section/SectionHeader";
import { useStrings } from "../strings";
import { styles } from "./AnnouncedBoard.styles";
import type { BoardGeometry } from "./board.constants";
import { DATE_WIDTH_EM, ERROR_HEIGHT_EM, PHONE_FLAP_SIZE, PHOTO_SHARE, SKELETON_ROWS } from "./board.constants";
import { BoardRow } from "./BoardRow";
import { BoardSkeletonRow } from "./BoardSkeletonRow";

export function AnnouncedBoard() {
  const strings = useStrings();
  const { width: screen } = useWindowDimensions();
  const [filters] = useState(() => ({ sort: "announced" as const, announced_from: announcedFrom(new Date()), limit: ANNOUNCED_COUNT }));
  const [apiBase] = useState(configuredApiBase);
  const [now] = useState(() => new Date());
  const { data, isPending, isError, refetch, hasNextPage } = useShows(filters);

  const shows = data?.pages[0].items ?? [];
  if (!isPending && !isError && shows.length === 0) return null;

  const geometry = boardGeometry(screen);
  return (
    <View style={styles.section}>
      <SectionHeader title={strings.sections.justAnnounced}>
        {shows.length > 0 ? <SectionAside>{strings.shows(shows.length, hasNextPage)}</SectionAside> : null}
      </SectionHeader>
      {isPending ? (
        <View style={styles.rows}>
          {Array.from({ length: SKELETON_ROWS }, (_, i) => (
            <BoardSkeletonRow key={i} geometry={geometry} />
          ))}
        </View>
      ) : isError ? (
        <SectionError onRetry={() => refetch()} minHeight={geometry.flapSize * ERROR_HEIGHT_EM} />
      ) : (
        <View style={styles.rows} role="list">
          {shows.map((show, i) => (
            <BoardRow key={show.id} show={show} index={i} now={now} apiBase={apiBase} geometry={geometry} />
          ))}
        </View>
      )}
    </View>
  );
}

function boardGeometry(screen: number): BoardGeometry {
  const layout = screen <= breakpoints.stacked ? "stacked" : "split";
  const flapSize = layout === "stacked" ? PHONE_FLAP_SIZE : fluid(typography.board.size, screen);
  return { flapSize, dateWidth: flapSize * DATE_WIDTH_EM[layout], photoShare: PHOTO_SHARE[layout] };
}
