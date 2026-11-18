import { useState } from "react";
import { Pressable, Text, View } from "react-native";
import type { Venue } from "../../../events/domain/venue";
import type { GroupBy, StripDay, When } from "../../application/explore";
import { venueChips } from "../../application/venue-filter";
import { Chip } from "../controls/Chip";
import { Segmented } from "../controls/Segmented";
import { useStrings } from "../strings";
import { CalendarModal } from "./CalendarModal";
import { ChipRow } from "./ChipRow";
import { DayStrip } from "./DayStrip";
import { styles } from "./ExploreFilters.styles";
import { SearchField } from "./SearchField";
import { VENUE_CHIPS } from "./explore.constants";
import { VenuePicker } from "./VenuePicker";
import type { ExploreFilters as Filters } from "./use-explore-filters";

type Props = {
  now: Date;
  filters: Filters;
  venues: Venue[];
  days: StripDay[];
  daysWithShows: Set<string>;
  active: boolean;
  onText: (text: string) => void;
  /** Adds the venue to the chosen ones, or takes it out. */
  onVenue: (venue: string) => void;
  onAllVenues: () => void;
  onWhen: (when: When) => void;
  onDay: (iso: string) => void;
  onGroup: (group: GroupBy) => void;
  onClear: () => void;
};

const WHEN_ORDER: Exclude<When, "day">[] = ["all", "today", "weekend", "week", "month"];
const GROUP_ORDER: GroupBy[] = ["day", "week", "month"];

export function ExploreFilters(props: Props) {
  const { explore } = useStrings();
  const { filters } = props;
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [venuesOpen, setVenuesOpen] = useState(false);
  const chips = venueChips(props.venues, filters.venues, VENUE_CHIPS);
  return (
    <View style={styles.panel} accessibilityRole="search">
      <SearchField value={filters.text} onChange={props.onText} />
      <ChipRow label={explore.venues} role="group">
        <Chip label={explore.allVenues} selected={filters.venues.length === 0} kind="checkbox" onPress={props.onAllVenues} />
        {chips.map((venue) => (
          <Chip key={venue} label={venue} selected={filters.venues.includes(venue)} kind="checkbox" onPress={() => props.onVenue(venue)} />
        ))}
        {props.venues.length > VENUE_CHIPS ? (
          <Chip label={explore.moreVenues(props.venues.length)} selected={false} kind="action" onPress={() => setVenuesOpen(true)} />
        ) : null}
      </ChipRow>
      {venuesOpen ? (
        <VenuePicker venues={props.venues} selected={filters.venues} onToggle={props.onVenue} onClose={() => setVenuesOpen(false)} />
      ) : null}
      <View style={styles.row}>
        <Text style={styles.label}>{explore.when}</Text>
        <ChipRow label={explore.when}>
          {WHEN_ORDER.map((when) => (
            <Chip key={when} label={explore.whenOptions[when]} selected={filters.when === when} onPress={() => props.onWhen(when)} />
          ))}
        </ChipRow>
      </View>
      <DayStrip
        now={props.now}
        days={props.days}
        withShows={props.daysWithShows}
        selected={filters.day}
        onSelect={props.onDay}
        onMore={() => setCalendarOpen(true)}
      />
      <CalendarModal
        visible={calendarOpen}
        today={props.days[0].iso}
        selected={filters.day}
        onPick={(iso) => {
          setCalendarOpen(false);
          if (iso !== filters.day) props.onDay(iso);
        }}
        onClose={() => setCalendarOpen(false)}
      />
      <View style={[styles.row, styles.spread]}>
        <View style={styles.row}>
          <Text style={styles.label}>{explore.groupBy}</Text>
          <Segmented
            options={GROUP_ORDER.map((value) => ({ value, label: explore.groupOptions[value] }))}
            value={filters.group}
            onChange={props.onGroup}
            accessibilityLabel={explore.groupBy}
          />
        </View>
        {props.active ? (
          <Pressable accessibilityRole="button" onPress={props.onClear} style={styles.clearTarget}>
            <Text style={styles.clear}>{explore.clear}</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}
