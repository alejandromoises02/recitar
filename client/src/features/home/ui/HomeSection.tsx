import { memo } from "react";
import type { HomeSection as Section } from "../application/home-layout";
import { AnnouncedBoard } from "./announced-board/AnnouncedBoard";
import { ExploreHeader } from "./explore/ExploreHeader";
import { FeaturedFan } from "./featured-fan/FeaturedFan";
import { NextUpStrip } from "./next-up/NextUpStrip";

const SECTIONS: Record<Section, () => React.JSX.Element | null> = {
  featured: FeaturedFan,
  justAnnounced: AnnouncedBoard,
  next: NextUpStrip,
  explore: ExploreHeader,
};

/** Memoised: typing in the explore search re-renders the screen, not the sections above it. */
export const HomeSection = memo(function HomeSection({ section }: { section: Section }) {
  const Component = SECTIONS[section];
  return <Component />;
});
