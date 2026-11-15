---
name: recitAR
description: All of Buenos Aires' live shows in one place, linking to the official ticket pages.
colors:
  night-ink: "#0E0D0C"
  marquee-cream: "#F4EEDF"
  cream-muted: "rgba(244, 238, 223, 0.6)"
  hairline: "rgba(244, 238, 223, 0.12)"
  glass: "rgba(255, 255, 255, 0.04)"
  marquee-yellow: "#F2C230"
  filete-red: "#B3241B"
  filete-blue: "#2E6FBF"
  flap-top: "#25221F"
  flap-bottom: "#1B1917"
  flap-hinge: "#0A0908"
  card-smoke: "rgba(18, 17, 16, 0.72)"
  sleeve-empty: "#1C1A18"
  badge-ink: "rgba(14, 13, 12, 0.88)"
  field-line: "rgba(244, 238, 223, 0.4)"
typography:
  logo:
    fontFamily: "Alfa Slab One, serif"
    fontSize: "30px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0em"
  display:
    fontFamily: "Unbounded, sans-serif"
    fontSize: "clamp(30px, 3.4vw, 72px)"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Unbounded, sans-serif"
    fontSize: "clamp(22px, 1.8vw, 36px)"
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Onest, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
  body-small:
    fontFamily: "Onest, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Onest, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.16em"
  marquee:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "clamp(17px, 1.2vw, 26px)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "0.06em"
    fontFeature: "tnum"
rounded:
  sleeve: "3px"
  flap: "4px"
  thumb: "9px"
  card-sm: "14px"
  card: "18px"
  pill: "999px"
spacing:
  hair: "4px"
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
  3xl: "64px"
components:
  button-primary:
    backgroundColor: "{colors.marquee-cream}"
    textColor: "{colors.night-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.pill}"
    padding: "6px 20px 6px 6px"
  button-icon:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.marquee-cream}"
    rounded: "{rounded.pill}"
    size: "44px"
  chip:
    backgroundColor: "transparent"
    textColor: "{colors.marquee-cream}"
    typography: "{typography.body-small}"
    rounded: "{rounded.pill}"
    padding: "8px 14px"
  chip-selected:
    backgroundColor: "{colors.marquee-yellow}"
    textColor: "{colors.night-ink}"
    rounded: "{rounded.pill}"
    padding: "8px 14px"
  tag-featured:
    backgroundColor: "{colors.marquee-yellow}"
    textColor: "{colors.night-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "4px 10px"
  flap-cell:
    backgroundColor: "{colors.flap-top}"
    textColor: "{colors.marquee-cream}"
    typography: "{typography.marquee}"
    rounded: "{rounded.flap}"
    height: "2em"
  spotlight-card:
    backgroundColor: "{colors.card-smoke}"
    textColor: "{colors.marquee-cream}"
    rounded: "{rounded.card}"
    padding: "22px 26px"
  show-card:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.marquee-cream}"
    rounded: "{rounded.card-sm}"
    padding: "10px"
  search-field:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.marquee-cream}"
    typography: "{typography.body-small}"
    rounded: "{rounded.pill}"
    height: "40px"
---

# Design System: recitAR

Source of truth: the approved home mock `.impeccable/mocks/home/home.html` (local, gitignored) and the home brief `.impeccable/surfaces/home.md`. The app implements these values from `client/src/design/tokens.ts`.

## Overview

**Creative North Star: "The Night Marquee"**

recitAR looks like Buenos Aires after dark: a theatre marquee lit in warm yellow over a near-black street, a hand-painted sign with a fileteado shadow, and a record bin you flick through. The page is dark and warm, never blue-black. Information sits on split-flap boards, and the one playful object is the record that slides out of its sleeve.

It is an Operate surface first: people come to see what was announced and to reach the official ticket page. Expression lives in a few precise signatures (the slab logo, the split-flap board, the record fan). Everything else is quiet: one text face, cream text, thin hairlines, pill controls.

**Key Characteristics:**
- Warm near-black ground (#0E0D0C) with cream text, not white.
- One accent, marquee yellow, for dates, selected states and calls to action.
- The slab logo face is the brand mark and appears only on "recitAR" and on "Buenos Aires".
- Lists of shows are split-flap boards in Barlow Condensed, uppercase, tabular numbers.
- Featured shows are a fan of record sleeves; the centre record slides out and is the play button for a Spotify sample.
- Motion carries meaning (a record changes, a board row flips, the record spins while music plays); the only decorative loop is the "live" pulse.

## Colors

A warm night palette: one yellow accent over ink and cream, with the fileteado red and blue kept for the brand mark.

### Primary
- **Marquee Yellow** (#F2C230): dates on the board, selected chips, the Featured tag, the ticket-button icon, the "+N fechas" count, focus rings. 11.6:1 on Night Ink.

### Secondary
- **Filete Red** (#B3241B): first step of the logo's stepped shadow; also the colour for alert tags. White text on it is 6.3:1.
- **Filete Blue** (#2E6FBF): last step of the logo's stepped shadow only.

### Neutral
- **Night Ink** (#0E0D0C): page background and text on yellow or cream surfaces.
- **Marquee Cream** (#F4EEDF): primary text and the primary button fill. 16.8:1 on Night Ink.
- **Cream Muted** (cream at 60%): secondary text (venues, metadata, section labels). About 6:1 on Night Ink and 5.8:1 on a flap.
- **Hairline** (cream at 12%): borders of cards, chips and dividers.
- **Field Line** (cream at 40%): the outline of text fields, 3:1 on Night Ink so the field reads as a field (WCAG 1.4.11).
- **Glass** (white at 4%): resting fill of chips, fields, icon buttons and show cards.
- **Flap Top / Flap Bottom** (#25221F / #1B1917): the two halves of a split-flap cell.
- **Flap Hinge** (#0A0908): the 1px hinge line behind the letters of a flap cell.
- **Card Smoke** (Night Ink at 72%): the spotlight card over the blurred cover tint.
- **Badge Ink** (Night Ink at 88%): small badges laid on photos (the date on show cards); dark enough that cream and muted text stay above 4.5:1 even over a white photo.

### Named Rules
**The One Light Rule.** Marquee Yellow is the only accent. It marks dates, selection and the way to tickets, and nothing else; never use it as a large fill behind text blocks.

**The Warm Dark Rule.** Backgrounds stay warm (#0E0D0C family). No blue-black, no pure #000, no pure #FFF text.

## Typography

**Brand Font:** Alfa Slab One (logo and "Buenos Aires" only)
**Display Font:** Unbounded (with sans-serif fallback)
**Body Font:** Onest (with system-ui fallback)
**Board Font:** Barlow Condensed (with sans-serif fallback)

**Character:** A wide, modern display face with a friendly humanist text face, set against a condensed board face that reads like a departures sign. The slab face is the painted sign above the door.

### Hierarchy
- **Logo** (Alfa Slab One 400, 30px desktop / 24px phone, line-height 1): "recitAR" with a stepped shadow of 0.06em red, 0.12em ink gap, 0.15em blue.
- **Display** (Unbounded 600, clamp(30px, 3.4vw, 72px), line-height 1, -0.035em): the page headline.
- **Headline** (Unbounded 500, clamp(22px, 1.8vw, 36px), line-height 1.1, -0.02em): the featured show name in the spotlight card and month titles.
- **Body** (Onest 400, 15px, line-height 1.45): descriptions and metadata lines.
- **Body small** (Onest 400, 13px): chips, fields, card metadata.
- **Label** (Onest 600, 11px, 0.16em, uppercase): section labels ("Recién anunciados", "Destacados", "Próximos") and the live kicker.
- **Marquee** (Barlow Condensed 700, clamp(17px, 1.2vw, 26px), 0.06em, uppercase, tabular numbers): every split-flap cell. Secondary cells (venue, time) use 0.78em and weight 600.

### Named Rules
**The Painted Sign Rule.** Alfa Slab One appears on two things only: the "recitAR" logo and the words "Buenos Aires" in the headline. Never on show names, buttons or labels.

**The Board Rule.** Show lists use Barlow Condensed uppercase with tabular numbers; prose and controls never do.

## Layout

- **Gutter:** clamp(16px, 3vw, 64px) on both sides; no max-width cap on the hero, so wide screens get bigger pieces instead of empty margins.
- **Hero (desktop, 901px and up):** two columns 40 / 60 (minmax(0, 4fr) / minmax(0, 6fr)), column gap clamp(28px, 4vw, 96px). Left: kicker, headline, Just announced board. Right: Featured fan, spotlight card, controls. Hero height min(100svh, 1040px).
- **Sizes scale with the viewport:** sleeve size clamp(220px, min(19vw, 34svh), 440px); board text clamp(17px, 1.2vw, 26px).
- **Below the hero:** a horizontal "Próximos" strip (about 4.4 cards visible on desktop, 250px cards swiped on phones), then "Toda la cartelera": a sticky filter panel and a card grid (repeat(auto-fill, minmax(230px, 1fr)), 16px gap) grouped by month, week or day.
- **Phones and tablets (900px and down):** one column in this order: header, headline, Featured fan and card, Just announced board, Próximos, explore. Board rows keep date plus name, with venue and "+N fechas" on a second line; the photo strip narrows to 30%. The filter panel stops being sticky.
- **Rhythm:** 4px between board rows, 8 to 12px inside groups, 24 to 56px between sections.

## Elevation & Depth

Depth comes from tonal layers and the photography, not from a shadow scale. The page ground is flat Night Ink; a blurred, low-opacity copy of the current featured cover (about 28%) tints the hero and changes with it. Cards sit on Glass or Card Smoke with a Hairline border.

### Shadow Vocabulary
- **Sleeve drop** (`box-shadow: 0 30px 60px -22px rgba(0, 0, 0, 0.9), inset 0 0 0 1px rgba(255, 255, 255, 0.08)`): record sleeves in the fan.
- **Record drop** (`box-shadow: 0 18px 40px -10px rgba(0, 0, 0, 0.8)`): the vinyl record.

### Named Rules
**The No Glow Rule.** No coloured glows or halos. Shadows are neutral black and only on physical objects (sleeves, record).

## Shapes

Physical objects are nearly square: sleeves 3px, flap cells 4px. Interface surfaces are soft: show cards 14px, the spotlight card 18px, thumbnails 9px. Every control (buttons, chips, fields, language toggle) is a full pill. The record and its label are circles. Flap cells split horizontally into two tones with a hairline hinge drawn behind the letters.

## Components

### Buttons
- **Shape:** full pill (999px).
- **Primary ("Ver fechas y entradas"):** Marquee Cream fill, Night Ink text, Onest 700 14px, padding 6px 20px 6px 6px, with a 38px Marquee Yellow circle holding the arrow at the start.
- **Hover / Press:** lifts 2px on hover (web only); scales to 0.97 on press. No glow.
- **Icon button:** 44px circle, Glass fill, Hairline border; hover fills with cream and turns the icon ink. Used for previous / next.
- **Pause button:** same as icon button but pill-shaped with a label ("Pausar" / "Reproducir"), aria-pressed.

### Chips
- **Style:** transparent with Hairline border, Onest 13px, padding 8px 14px.
- **Selected:** Marquee Yellow fill, Night Ink text, weight 600. Date chips are single choice; venue chips toggle.

### Cards / Containers
- **Spotlight card:** Card Smoke fill, Hairline border, 18px radius, padding about 22px 26px. Top row: Featured tag (yellow pill) and the full date (DD/MM/YYYY with weekday). Then the show name (Headline), venue plus "+N fechas", the primary button with the ticket domain, and a trust line "recitAR no vende entradas: te lleva a la página oficial de cada show." A 3px yellow progress bar along the bottom edge shows the autoplay timer.
- **Show card (Próximos):** Glass fill, Hairline border, 14px radius, 10px padding, 72px thumbnail (9px radius), a yellow uppercase "en N días" label, name and venue with date.
- **Missing image:** a typographic fallback (initials or name in Unbounded on a warm brown radial gradient), never an empty box.

### Inputs / Fields
- **Style:** Glass fill, Hairline border, pill, 40px tall, Onest 13px, cream placeholder at 60%.
- **Focus:** border turns Marquee Yellow; a 2px yellow focus ring with 3px offset on keyboard focus.

### Navigation
- Header: logo, text links (Onest 13px, Cream Muted, cream when active), search field, ES / EN segmented pill (active segment cream with ink text). On phones the links and field collapse to a 44px search icon button.

### Split-flap Board (signature)
- Used for Just announced only. Each row is a link: a date cell (yellow) and a name cell (cream) with venue and "+N fechas" under the name.
- Cells use the two-tone flap fill and a hinge line behind the letters, so it never reads as strikethrough.
- A photo strip fills the right 38% of the name cell (30% on phones), inset 4px, 3px radius, fading in from the left; the hinge line crosses it too. Rows without a photo stay text only.
- Rows flip in from rotateX(-90deg) with a 70ms stagger when they appear.

### Record Fan (signature)
- Up to about 8 featured sleeves on an arc: the centre sleeve straight and full brightness; neighbours shift sideways, drop, tilt 5.5 degrees per step, shrink 7% per step and dim to 58% brightness; beyond 2.6 steps they fade out. Edges fade with a horizontal mask.
- The record is 64% of the sleeve width and slides out to the right (0.72 x sleeve width; 0.66 on phones, where the whole fan shifts left so the record stays on screen), with the show image as its label and the name on a text ring.
- The record is the play button for the Spotify sample: a yellow ▶ badge sits on its label; it spins at 33 rpm (1.8s per turn) only while the sample plays. No badge when the show has no Spotify match.
- Changing show: the record slides back in, the sleeves move, the new record slides out, and any playing sample stops. Autoplay every 7s; pauses on hover or focus; stops for good once the visitor touches, drags or uses the arrows, or while a sample plays; visible pause button above the card; screen readers hear manual changes only.

### Spotify Player
- The official compact Spotify embed (80px tall, 12px radius) inside the spotlight card, always visible with Spotify's own branding, controlled from the record through Spotify's iFrame API. Never hidden or restyled. Hidden entirely when the show has no Spotify match.

### Explore ("Toda la cartelera")
- **Filter panel:** card-smoke panel, Hairline border, 18px radius, 16px padding, sticky on desktop. Rows: search field plus venue select plus type chips; "Cuándo" chips (any date, today, this weekend, this week, this month, date range with two date fields); a strip of the next 14 days (58px tiles, 12px radius, weekday label, day number in Unbounded, yellow dot when a day has shows, yellow fill when selected); "Ver por" segmented control (Mes / Semana / Día) and a yellow underlined "Limpiar filtros" when a filter is active.
- **Group headings:** Unbounded 500, clamp(18px, 1.5vw, 26px), with a count label; "Hoy", "Mañana" and "esta semana" in yellow.
- **Show card:** Glass fill, Hairline border, 14px radius; photo 4:3 with a date block (Barlow Condensed: weekday, day in yellow, month) at top left and a yellow "+N fechas" pill at top right; body with the name (Onest 600 16px, two lines max), venue · time, and a type tag. Hover lifts 3px. Without a photo, initials on the warm gradient.
- **Empty result:** dashed panel with "No hay shows con esos filtros." and a clear-filters button.

## Do's and Don'ts

### Do:
- **Do** keep Marquee Yellow (#F2C230) for dates, selection and ticket actions only.
- **Do** write dates in one family: "VIE 19/03" on boards, "VIE 19/03/2027" in the spotlight card; compute weekdays, never type them.
- **Do** show "+N fechas" wherever a show has more dates.
- **Do** keep the trust line that recitAR does not sell tickets next to the ticket action.
- **Do** honour reduced motion: no autoplay, no spinning, instant swaps.

### Don't:
- **Don't** use Alfa Slab One anywhere except the logo and "Buenos Aires".
- **Don't** add coloured glows, halos or pulsing decorations; the only loops are the record spinning while a sample plays and the live pulse dot.
- **Don't** play sound on its own; audio starts only from a tap on the record or the Spotify player.
- **Don't** draw the flap hinge over the letters (it reads as "cancelled").
- **Don't** repeat the same shows in two hero blocks: the board is Just announced, the fan is Featured.
- **Don't** use the split-flap board for the full agenda; explore uses show cards so it reads differently from the hero.
- **Don't** use pure black or pure white.
