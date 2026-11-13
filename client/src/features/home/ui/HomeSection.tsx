import type { HomeSection as Section } from "../application/home-layout";
import { AnnouncedBoard } from "./announced-board/AnnouncedBoard";
import { SLOT_HEIGHT } from "./home.constants";
import { NextUpStrip } from "./next-up/NextUpStrip";
import { SectionSlot } from "./SectionSlot";

export function HomeSection({ section }: { section: Section }) {
  if (section === "next") return <NextUpStrip />;
  if (section === "justAnnounced") return <AnnouncedBoard />;
  return <SectionSlot section={section} minHeight={SLOT_HEIGHT[section]} />;
}
