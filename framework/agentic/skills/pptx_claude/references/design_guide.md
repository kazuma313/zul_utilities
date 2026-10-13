# Design guide

The script handles fonts, spacing and colours. Your job is structure and wording.

## Deck structure

1. Start with `title`.
2. Decks over 8 slides: add `agenda` second and `section_divider` before each part.
3. Do not repeat a layout on consecutive slides.
4. Include at least one visual slide: `stat_callout`, `chart`, `quote`, `icon_grid` or `timeline`.
5. End with `conclusion_cta`. The `cta` is one action, not a summary.

## Pick the layout from the content

| The content is ... | Use |
|---|---|
| 2 to 4 important numbers | `stat_callout` |
| numbers over time or by category | `chart` (`line` for time, `bar` for categories, `pie` for shares of a whole with at most 6 slices) |
| many values with 2+ attributes | `table` |
| A versus B | `two_column` (sentences) or `two_column_bullets` (lists) |
| 3 to 6 parallel ideas | `icon_grid` |
| a term that needs explaining | `definition` |
| steps in time order | `timeline` (up to 5) |
| ordered steps or principles with explanations | `numbered_list` |
| risks or problems | `challenges` |
| someone's words | `quote` |
| a short explanation | `content` |
| anything else | `bullets` |

## Patterns

| Deck | Layout order |
|---|---|
| Investor pitch | title, stat_callout, challenges, icon_grid, chart, timeline, conclusion_cta |
| Teaching a topic | title, definition, icon_grid, numbered_list, two_column, quote, conclusion_cta |
| Project review | title, agenda, stat_callout, timeline, challenges, table, conclusion_cta |
| Team update | title, bullets, stat_callout, table, conclusion_cta |
| Proposal | title, content, two_column, features_stats, timeline, table, conclusion_cta |

## Wording

- Titles state the point: "Churn fell 30% after onboarding redesign", not "Churn".
- One idea per bullet, under 12 words, no full stop at the end.
- Parallel grammar inside a list (all start with a verb, or all are noun phrases).
- Numbers: round them (`"4.2M"`, not `"4,198,331"`), keep the unit in `value`.
- Write everything in the language the user asked for, including `cta` and the `conclusion_cta` title.

## Themes

| Theme | Dark / accent | Good for |
|---|---|---|
| `midnight` | navy / cyan | corporate, executive |
| `coral` | indigo / coral red | marketing, startups |
| `forest` | green / moss | sustainability, agriculture |
| `ocean` | deep blue / cyan | technology, finance |
| `charcoal` | slate / mint | minimal, modern |
| `cherry` | red / gold | bold announcements |

One theme per deck. Per-slide backgrounds (`bg_override`) are ignored unless the
script is called with `--allow-bg-override`, because models tend to pick clashing colours.

## Avoid

- More than 6 items in any list.
- The same layout for every slide.
- Icons from different families, or icons mixed with emoji, on one slide.
- Invented statistics. If the user gave no numbers, use qualitative layouts.
- Paragraphs in `bullets`, and bullets in `content`.
