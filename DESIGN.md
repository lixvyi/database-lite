# Design System — 拾页图书室

## Direction

The interface translates a physical library circulation ledger into a calm desktop workbench. It uses paper, ink, indexing, and stamped state as functional structure rather than decoration.

## Palette

- Warm paper `#F3EEDF` and light work surface `#FBF8EE`
- Deep library ink `#173A32`
- Vermilion action stamp `#C84A32`
- Olive secondary state `#74806A`
- Charcoal content `#202923`
- Ledger rule `#D7D0BD`

No gradients, glow, glass, or decorative texture overlays.

## Typography

- Product name and page titles: Chinese Song/serif, editorial and authoritative.
- Controls, labels, forms, and tables: Chinese UI sans-serif.
- Metrics and counts: serif with tabular numerals.

## Layout and Components

- Fixed 224px dark sidebar; one continuous paper work surface.
- Data tables and ruled bands are primary containers. Avoid nested cards.
- Primary action is a restrained vermilion rectangle with 10px radius.
- Status stamps use text, border, and fill together; color is not the only signal.
- Dialogs are reserved for short create/transaction flows requiring focused completion.

## Interaction

- Selected navigation inverts to paper on ink.
- Hover clarifies actionable rows without moving layout.
- Focus rings are warm vermilion and always visible.
- One short toast movement confirms completed transactions; reduced-motion disables it.

## Desktop Scope

Optimized for a desktop browser window at 1440×900 and above. The project intentionally does not include a mobile layout.
