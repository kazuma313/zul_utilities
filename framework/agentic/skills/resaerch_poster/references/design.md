# Design notes

Two presets, both taken from reference posters:

- `blue` ("Blue and White Modern Consumer Research Poster"): numbered bar headers, dark blue corner shape, italic subtitle, centred contact footer.
- `purple` ("Technology - shaping a better future"): rounded pill headers with an icon disc, wave lines behind the title, faint grid and circles on the page, a gradient banner footer with a slogan, no numbers.

## Layout

Sections sit in rows of a 12-column grid (`width`: narrow 4, half 6, wide 8, full 12; automatic from the amount of content when missing). Rows are content-sized, so a row with a chart is taller than a row with two short paragraphs, and a full-width `columns` section spreads its groups across the page. This is what makes the page look designed rather than like a spreadsheet. `"layout": "grid"` restores equal cards in two columns.

Fitting in flow layout: after the fonts load, the whole grid is scaled (55 % to 145 %) until the rows fill the page height, then every card that is shorter than its row enlarges its own text (up to about 150 %) as long as the row does not grow. Charts scale with the text. If the floor is reached the grid gets `data-overflow` in the HTML and the bottom is clipped: shorten texts or drop a section.

## The blue reference

- Page background light grey-lilac (#ECEBF3) with white diagonal stripes; dark blue corner shape top right.
- Header: dark blue tag pill, three-line uppercase title in Poppins 800 with one word in blue, italic subtitle with a short blue underline, rounded hero picture top right, small white icons and a dot grid in the corner.
- Cards: white, dark blue border and header bar, light blue number box with an arrow-shaped edge, uppercase title.
- Body: icon discs in pale blue, big blue numbers, donut chart in blue / light blue / orange / lilac / red, quote box in pale blue.
- Footer: dark blue bar with the contact line.

Everything is sized in `--u` = 1 % of the page width, so the poster looks the same at every paper size. The number of rows sets the base font size (4 rows = 8 sections is the densest).

## Fitting in grid layout

Every card is measured separately: the text shrinks in 3 % steps down to 50 % until it fits its equal-height cell, or grows up to 130 %. A card that still overflows is marked `data-overflow`.

## Theme overrides

```json
"theme": {"preset": "purple", "primary": "#5B21B6", "accent": "#A855F7", "ink": "#1E1B4B", "muted": "#5B5B7A",
          "page": "#F3EEFB", "card": "#FFFFFF", "soft": "#EDE4FB", "header_style": "pill", "numbered": false,
          "palette": ["#5B21B6", "#A855F7", "#F5B453", "#60A6F7", "#EF737C"]}
```

Any subset works; `"theme": "purple"` alone selects the preset. `header_style` is `bar` or `pill`, `numbered` shows 01, 02 ... in the headers. `primary` is the dark colour (headers, footer, title accent), `accent` the light one (number boxes, tag), `palette` the chart colours in order.

## Fonts

Poppins (SIL Open Font Licence) is embedded in every HTML as base64, so the poster renders the same on any computer. The reference used Etna for the title; Poppins ExtraBold is the closest open font.

## Output

- `.html`: self-contained single file (fonts and images inline), about 150 KB plus images. Opens in any browser; print to PDF with margins set to none.
- `.pdf`: one page at the chosen paper size, vector text and charts, printed by a headless Chromium (Edge, Chrome, Chromium or playwright).
- `.png`: 96 dpi screenshot of the page (A2 = 1587 x 2245 px) for previews and chat.
