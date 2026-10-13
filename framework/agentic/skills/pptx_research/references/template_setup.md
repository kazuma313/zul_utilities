# The template file

`assets/template.pptx` is a size-reduced copy of
`Black and White Modern Research Proposal Presentation.pptx` (15 slides, 20 x 11.25 inches).
The builder copies slides from it, so all shapes, gradients, photos and the embedded fonts come from that file.
The code contains no design of its own.

## Rebuilding assets/template.pptx

```
python scripts/prepare_template.py "C:\path\Black and White Modern Research Proposal Presentation.pptx"
```

The original is about 25 MB because some photos are 5000+ pixels wide. The script writes a copy with photos of
at most 2000 px (about 6 MB). Decks built from it are about 3 MB. The original file is not changed.
You can also point the builder at another copy: `--template file.pptx` or `PPTX_RESEARCH_TEMPLATE`.

## What you may change in the template

Safe: swap photos, change colours, change fonts, edit the placeholder text (its **length** is used as the
capacity of each text box, so keep it about as long as the space allows).

Not safe: renaming or deleting shapes, regrouping, deleting or re-ordering slides. The builder finds shapes by
name (`TextBox 5`, `Group 12` ...) and slides by number. If a shape is missing the build stops with
`template shape '...' not found`.

## Fonts

The template uses HK Grotesk, Open Sauce and Open Sans, embedded in the file. PowerPoint for Windows uses the
embedded fonts. Keynote, Google Slides, LibreOffice and older PowerPoint for Mac versions ignore them and substitute
another font, which makes big titles wrap differently. For those programs install the fonts (all three are free,
open-licence fonts), or export to PDF from PowerPoint for Windows.

`scripts/render_preview.py` uses LibreOffice, so without the fonts installed its images show wider titles than
PowerPoint will.

## Licence of the template

The template and its stock photos come from the template vendor (Canva) under their content licence, not from
this skill. Use decks you build from it in your own work as that licence allows. Do not publish or share
`assets/template.pptx` itself, or this skill folder with the template inside, as a template for other people.
To share the skill, remove `assets/template.pptx` and let each user add their own copy with `prepare_template.py`.
