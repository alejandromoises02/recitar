import type { HomeSection } from "../application/home-layout";

export const NEXT_UP_COUNT = 8;
export const ANNOUNCED_COUNT = 12;
export const EXPLORE_PREVIEW_COUNT = 20;

/** Placeholder heights for sections not built yet, so the frame already reads like the mock. */
export const SLOT_HEIGHT: Record<HomeSection, number> = { featured: 420, justAnnounced: 360, next: 200, explore: 480 };
