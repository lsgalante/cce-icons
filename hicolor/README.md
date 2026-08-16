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
