import type { EventCategory } from "../domain/event";

/**
 * The only kind of event the app shows in this first phase. The server stores every kind; every
 * list the app asks for (home sections, venues, "more at") sends it as `category`. Theatre and the
 * rest come later: widen the API filter first, then this.
 */
export const VISIBLE_CATEGORY: EventCategory = "concert";
