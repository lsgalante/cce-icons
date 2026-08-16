# cce cursor theme

A full XCursor theme in the cce language: **white fill, `#282a36` outline**, with
a rounded **plus** as the default pointer rather than an arrow (it follows the
earlier `crosshair-theme` experiment, and matches `svg/plus.svg` in the icon set).

```
svg/        the sources — one SVG per distinct shape, 32x32 viewBox
build.py    svg -> PNG (magick) -> XCursor binary + alias symlinks
dist/       build output (untracked)
```

## Build

```sh
python3 build.py              # -> dist/cce
python3 build.py --install    # -> $XDG_DATA_HOME/icons/cce
python3 build.py --only text  # rebuild one cursor while iterating
```

`xcursorgen` is **not** required: `build.py` writes the XCursor container itself
(header, per-size TOC, premultiplied BGRA image chunks). Sizes are 24/32/48/64/96,
covering scale 1 through 4 at a 24px nominal cursor.

## Using it

The theme installs to `~/.local/share/icons/cce` but nothing selects it. The
compositor asks for the theme literally named **`default`** — `Cursor::init`
passes a null theme name to `wlr_xcursor_manager_create`, which does *not* read
`$XCURSOR_THEME`. So point the `default` theme at this one:

```ini
# ~/.local/share/icons/default/index.theme
[Icon Theme]
Name=Default
Inherits=cce
```

That covers GTK and Qt apps too. (`ccectl` has no cursor-theme command; the other
route is the `cce-window-management` protocol's `set_xcursor_theme`, which reaches
`Cursor::set_theme`.)

## Adding or changing a cursor

1. Drop a 32x32 SVG in `svg/`.
2. Add a row to `CURSORS` in `build.py`: `(name, svg stem, hotspot x, hotspot y, [aliases])`.
   Hotspots are in **source viewBox units** and are scaled per size.
3. Rebuild.

The alias lists are load-bearing, not decoration: GTK and Qt still request X11
legacy names (`xterm`, `fleur`, `sb_v_double_arrow`) and hashed names
(`00008160000006810000408080010102`). A missing alias is the usual reason a theme
looks half-applied in one toolkit.

Cursors with a state badge (`copy`, `alias`, `help`, `context-menu`, `progress`)
use a compact plus in the upper-left with the badge lower-right, so their hotspot
is `(11,11)`, not the centre.

## Animation

Every cursor here is single-frame. The compositor *can* drive animated cursors —
see `Cursor::advance_xcursor_frame` in cce-compositor, which walks XCursor's
per-frame delays — so an animated `wait`/`progress` only needs extra frames:
give `build.py` a list of SVGs per cursor and a delay, and emit one image chunk
per frame per size (the container already supports it; `xcursor()` takes a
`delay` field it currently always writes as 0).
