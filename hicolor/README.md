# App icons (`hicolor/`)

The XDG icon theme cce apps are looked up in. `ccebuild install` mirrors this
tree into `$XDG_DATA_HOME/icons/hicolor/`, so **the path here is the path there** —
the size and context of an icon are its directory (`scalable/apps`), not a rule
buried in the installer. Adding `48x48/apps/` or `scalable/mimetypes/` later needs
no change to `ccebuild`.

## Why `hicolor` and not the `cce` theme

`hicolor` is the spec-mandated fallback: every implementation searches it last, no
matter what the user's icon theme is set to. The sibling `cursors/` theme installs
as `~/.local/share/icons/cce` and, as its README notes, **nothing selects it** —
there is no icon-theme setting anywhere in the DE. An app icon put there would
resolve for nobody. Putting them in `hicolor` means they resolve unconditionally.

Deliberately **no `index.theme` here.** The system `hicolor-icon-theme` package
already ships one at `/usr/share/icons/hicolor/index.theme` declaring every
size/context directory, and a theme is the union of its per-base-dir trees. A
second index in `$XDG_DATA_HOME` that listed only `scalable/apps` would be read
first and make every other hicolor directory invisible.

## Every file is a symlink into `../../../svg/`

`svg/` stays the sole source (see the design-language notes there). An entry here
is a *name*, not artwork: `cce-files.svg -> ../../../svg/folder.svg` says "the
Files app is drawn with the folder glyph", and the glyph itself is edited in one
place. The link is intra-repo, so it never dangles in a standalone clone; `install`
dereferences it and writes a real file to the destination.

## Adding an app

1. The name must equal the `Icon=` key in the crate's `<crate>.desktop`, which by
   convention is the binary name. `Icon=cce-files` ⇒ `cce-files.svg`.
2. `ln -s ../../../svg/<glyph>.svg cce-<app>.svg` — or add a new glyph to `svg/`
   first if none fits.
3. `ccebuild install` picks it up with no edit to the installer.

## Third-party apps (`svg/apps/`)

cce also draws its own icons for apps it does not ship — Firefox, Steam,
Houdini, every entry the launcher lists — so the launcher and the Super-Tab
switcher read as one set rather than a wall of vendor logos. Their glyphs live
in `svg/apps/`, kept out of `svg/` itself because that directory is the flat
widget-glyph namespace `cce_ui::upload_icon` reads by bare name. They follow
the same language as the rest: white, 40×40, back layers at 0.55, lighting
facets at 0.7/0.42, dark accents in `#282a36` at 0.35.

Each is installed under one of two names, and which one matters:

- **The entry's `Icon=` value** when that is an app-specific theme name
  (`Icon=steam` ⇒ `steam.svg`). `$XDG_DATA_HOME/icons` is the first base dir
  every lookup searches, so this wins over the vendor's icon in
  `/usr/share/icons` for any consumer, not just cce's.
- **The desktop-file ID** (the `.desktop` file's stem) when `Icon=` cannot be
  overridden by name: an absolute path (`houdini.svg` for
  `Icon=/opt/hfs/houdini_logo.png`), missing (`raindropio.svg`), or a generic
  name several apps share (`avahi-discover`, `bssh` and `bvnc` all say
  `Icon=network-wired`; `qt5ct`/`qt6ct` say `preferences-desktop-theme`).
  Only cce-cloud honours these — it checks for
  `hicolor/scalable/apps/<id>.svg` before reading `Icon=` (`icon_override`) —
  so a new ID-named icon reaches the launcher and switcher and nothing else.

A versioned ID (`com.sidefx.houdini22.0.429.svg`) goes stale on the next
upgrade; re-point it when the entry is renamed. Several names can share one
glyph (all four Houdini entries do), and the links say so.
