# Section order and agenda

The builder guarantees that every deck follows one order, so the agenda numbers always match the slides.

## Standard order

| Rank | Layout | Typical section |
|---|---|---|
| 0 | `cover` | Title |
| 1 | `intro` | Hello, summary |
| 2 | `agenda` | Agenda |
| 3 | `section` | Background of the study |
| 4 | `three_cards` | Problem statement, objectives, research questions |
| 5 | `team` | Framework, literature, theorists |
| 6 | `two_cards` | Methodology |
| 7 | `people` | Qualitative data, participants |
| 8 | `chart` | Quantitative data |
| 9 | `timeline` | Proposed timeline |
| 10 | `analysis` | Analysis |
| 11 | `stat_chart` | Findings, key number |
| 12 | `gallery` | Portfolio |
| 13 | `testimonials` | Testimonials |
| 99 | `closing` | Thank you |

## Rules the builder applies

1. Slides are sorted by rank. Slides with the same layout keep the order you wrote them in.
2. `section` slides:
   - A background slide (layout `background` / `latar_belakang`, or a title that contains "background", "latar belakang", "pendahuluan") has rank 3.
   - Any other `section` slide travels with the slide that follows it in your JSON (it becomes that slide's header).
   - A `section` slide with nothing after it stays behind the slide before it.
3. Exactly one `cover` (extra covers become `section` slides) and one `closing` at the end (added when missing).
4. `organization` and `tagline` from the top of the JSON are shown on both the cover and the closing slide.
5. Agenda:
   - Items are the titles of the content slides (rank 3 to 13) in final order, numbered 01, 02 ...
   - Your own `items` are replaced, so the agenda can never disagree with the slides. Add `"auto": false` to an agenda slide to keep your items.
   - When there is no agenda slide and the deck has 4 or more sections, one is inserted after the intro.
   - The template has 8 rows. With more than 8 sections only the first 8 are listed (warning). Unused rows are removed.
   - A title longer than 34 characters is cut at a word boundary in the agenda. Give a slide `"agenda_label": "Short name"` to choose the wording.
6. Every change is reported, for example:
   `slides were re-ordered to the standard section order: cover > section > three_cards > ...`

## Switches

```
python scripts/build_deck.py deck.json -o out.pptx --keep-order   # keep the order of the JSON
python scripts/build_deck.py deck.json -o out.pptx --no-agenda    # never insert an agenda
```

Python: `build_deck(spec, "out.pptx", keep_order=True, auto_agenda=False)`.
