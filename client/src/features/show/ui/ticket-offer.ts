import { trackedTicketUrl } from "../../home/application/ticket-target";
import type { TicketPlan } from "../application/show-page";
import type { ShowStrings } from "./strings";

export type OfferLink = { url: string; label: string; detail?: string; hint: string };
export type TicketOffer = { links: OfferLink[]; note: string | null };

/** The ticket buttons and the line under them for a plan, in the page language. Each button opens the API's /go address, which counts the click. */
export function ticketOffer(plan: TicketPlan, when: string, strings: ShowStrings, apiBase: string): TicketOffer {
  if (plan.kind === "not-on-sale") {
    return {
      links: [{ url: trackedTicketUrl(apiBase, plan.eventId, null, "show"), label: strings.seeOn(plan.source.domain), hint: strings.opensNewTab }],
      note: strings.notOnSaleNote,
    };
  }
  const several = plan.targets.length > 1;
  const links = plan.targets.map((target) => {
    const base = plan.kind === "date" ? strings.tickets : strings.anyDate;
    return {
      url: trackedTicketUrl(apiBase, plan.eventId, target.vendor, "show"),
      label: several && target.vendor ? `${base} · ${target.vendor}` : base,
      detail: plan.kind === "date" ? when : undefined,
      hint: `${target.domain}. ${strings.opensNewTab}`,
    };
  });
  const domain = plan.targets[0].domain;
  if (plan.kind === "any-date") return { links, note: strings.pickOnSite(domain) };
  return { links, note: several ? null : `${strings.ticketsAt} ${domain}` };
}
