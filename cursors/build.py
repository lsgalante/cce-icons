#!/usr/bin/env python3
"""Build the `cce` XCursor theme from the SVG sources in ./svg.

Renders each source at every size in SIZES, adds the soft dark halo that keeps
a white cursor legible on white content, and writes the XCursor binary format
directly -- `xcursorgen` is not a dependency (it isn't packaged on this
machine, and the format is a header plus one chunk per image).

Output lands in ./dist/cce (untracked). `--install` copies it to
$XDG_DATA_HOME/icons/cce.

Cursor names come from CURSORS below: each entry maps an SVG to its hotspot
(in the 32x32 source viewBox) and every name that should resolve to it --
freedesktop names, X11 legacy names, and the MD5-looking names GTK/Qt still
ask for. Missing aliases are the usual reason a theme "doesn't work" in some
app, so they are part of the data, not an afterthought.
"""

import argparse
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG_DIR = HERE / "svg"
DIST = HERE / "dist" / "cce"

# Covers scale 1 through 4 at a 24px nominal cursor.
SIZES = [24, 32, 48, 64, 96]
VIEWBOX = 32.0

# Soft dark halo, in source-viewBox units, scaled per size.
SHADOW_BLUR = 0.55
SHADOW_OFFSET = (0.25, 0.4)
SHADOW_ALPHA = 0.55

# name -> (svg stem, hotspot x, hotspot y, [aliases])
# Hotspots are in the 32x32 viewBox.
CURSORS = [
    ("default", "plus", 16, 16, [
        "left_ptr", "arrow", "top_left_arrow", "top_left_corner_arrow",
        "default", "pointer-arrow",
    ]),
    ("crosshair", "crosshair", 16, 16, ["cross", "tcross", "cross_reverse"]),
    ("text", "text", 16, 16, ["xterm", "ibeam"]),
    ("vertical-text", "vertical-text", 16, 16, ["vertical_text"]),
    ("pointer", "pointer", 12, 4, [
        "hand", "hand1", "hand2", "pointing_hand",
        "9d800788f1b08800ae810202380a0822",  # hand2
        "e29285e634086352946a0e7090d73106",  # hand2
    ]),
    ("progress", "progress", 11, 11, [
        "half-busy", "left_ptr_watch",
        "08e8e1c95fe2fc01f976f1e063a24ccd",
        "3ecb610c1bf2410f44200f48c40d3599",
        "00000000000000020006000e7e9ffc3f",
        "9116a3ea924ed2162ecab71ba103b17f",
    ]),
    ("wait", "wait", 16, 16, ["watch", "clock"]),
    ("help", "help", 11, 11, [
        "question_arrow", "whats_this", "dnd-ask", "left_ptr_help",
        "5c6cd98b3f3ebcb1f9c7f1c204630408",
        "d9ce0ab605698f320427677b458ad60b",
    ]),
    ("context-menu", "context-menu", 11, 11, []),
    ("not-allowed", "not-allowed", 16, 16, [
        "forbidden", "crossed_circle", "circle",
        "03b6e0fcb3499374a867c041f52298f0",
    ]),
    ("no-drop", "not-allowed", 16, 16, [
        "dnd-none", "dnd_no_drop",
        "b66166c04f8c3109214a4fbd64a50fc8",
    ]),
    ("copy", "copy", 11, 11, [
        "dnd-copy", "copycur",
        "1081e37283d90000800003c07f3ef6bf",
        "6407b0e94181790501fd1e167b474872",
    ]),
    ("alias", "alias", 11, 11, [
        "dnd-link", "link",
        "640fb0e74195791501fd1ed57b41487f",
        "a2a266d0498c3104214a47bd64ab0fc8",
    ]),
    ("move", "move", 16, 16, [
        "fleur", "size_all", "all-scroll", "dnd-move",
        "4498f0e0c1937ffe01fd06f973665830",
        "fcf21c00b30f7e3f83fe0dfd12e71cff",
        "38c5dff7c7b8962045400281044508d2",
    ]),
    ("grab", "grab", 16, 16, ["openhand", "hand1-grab"]),
    ("grabbing", "grabbing", 16, 16, [
        "closedhand", "dnd-grabbing",
        "08ffe1cb5fe6fc01f906f1c063814ccf",
        "5aca4d189052212118709018842178c0",
    ]),
    ("cell", "cell", 16, 16, ["plus"]),
    ("zoom-in", "zoom-in", 14, 14, ["zoom_in"]),
    ("zoom-out", "zoom-out", 14, 14, ["zoom_out"]),
    ("ns-resize", "ns-resize", 16, 16, [
        "n-resize", "s-resize", "row-resize", "v_double_arrow",
        "sb_v_double_arrow", "split_v", "double_arrow", "size_ver",
        "top_side", "bottom_side", "based_arrow_up", "based_arrow_down",
        "00008160000006810000408080010102",
        "2870a09082c103050810ffdffffe0204",
    ]),
    ("ew-resize", "ew-resize", 16, 16, [
        "e-resize", "w-resize", "col-resize", "h_double_arrow",
        "sb_h_double_arrow", "split_h", "size_hor",
        "left_side", "right_side",
        "028006030e0e7ebffc7f7070c0600140",
        "14fef782d02440884392942c11205230",
    ]),
    ("nesw-resize", "nesw-resize", 16, 16, [
        "ne-resize", "sw-resize", "size_bdiag", "fd_double_arrow",
        "top_right_corner", "bottom_left_corner",
        "fcf1c3c7cd4491d801f1e1c78f100000",
    ]),
    ("nwse-resize", "nwse-resize", 16, 16, [
        "nw-resize", "se-resize", "size_fdiag", "bd_double_arrow",
        "top_left_corner", "bottom_right_corner",
        "c7088f0f3e6c8088236ef8e1e3e70000",
    ]),
    ("pencil", "pencil", 5, 27, ["draft", "draft_large", "draft_small"]),
    ("up-arrow", "up-arrow", 16, 4, ["center_ptr", "sb_up_arrow"]),
]

XC_IMAGE = 0xFFFD0002


def render(svg: Path, size: int):
    """Render `svg` at `size`x`size` and composite the halo. Returns RGBA bytes."""
    from PIL import Image, ImageFilter

    out = subprocess.run(
        ["magick", "-background", "none", "-density", str(int(size / VIEWBOX * 96)),
         str(svg), "-resize", f"{size}x{size}", "png32:-"],
        check=True, capture_output=True,
    ).stdout
    import io
    img = Image.open(io.BytesIO(out)).convert("RGBA")
    if img.size != (size, size):
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
        img = canvas

    scale = size / VIEWBOX
    blur = SHADOW_BLUR * scale
    if blur > 0.05:
        alpha = img.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
        alpha = alpha.point(lambda a: int(a * SHADOW_ALPHA))
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        shadow.putalpha(alpha)
        dx = int(round(SHADOW_OFFSET[0] * scale))
        dy = int(round(SHADOW_OFFSET[1] * scale))
        canvas = Image.new("RGBA", img.size, (0, 0, 0, 0))
        canvas.paste(shadow, (dx, dy), shadow)
        img = Image.alpha_composite(canvas, img)
    return img.tobytes()


def xcursor(frames):
    """Serialize [(size, w, h, xhot, yhot, delay, rgba)] into XCursor bytes.

    Pixels go out as premultiplied ARGB32 little-endian, i.e. B,G,R,A on the
    wire -- the layout libXcursor and wlroots both read back.
    """
    ntoc = len(frames)
    header = struct.pack("<4sIII", b"Xcur", 16, 0x10000, ntoc)
    toc_size = ntoc * 12
    pos = 16 + toc_size
    toc, chunks = b"", b""
    for size, w, h, xhot, yhot, delay, rgba in frames:
        toc += struct.pack("<III", XC_IMAGE, size, pos)
        body = bytearray(w * h * 4)
        for i in range(0, len(rgba), 4):
            r, g, b, a = rgba[i], rgba[i + 1], rgba[i + 2], rgba[i + 3]
            body[i] = b * a // 255
            body[i + 1] = g * a // 255
            body[i + 2] = r * a // 255
            body[i + 3] = a
        chunk = struct.pack("<IIIIIIIII", 36, XC_IMAGE, size, 1,
                            w, h, xhot, yhot, delay) + bytes(body)
        chunks += chunk
        pos += len(chunk)
    return header + toc + chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true",
                    help="copy the built theme into $XDG_DATA_HOME/icons/cce")
    ap.add_argument("--only", help="build just this cursor name (fast iteration)")
    args = ap.parse_args()

    cursors_out = DIST / "cursors"
    cursors_out.mkdir(parents=True, exist_ok=True)

    built, skipped, links = 0, [], 0
    for name, stem, hx, hy, aliases in CURSORS:
        if args.only and name != args.only:
            continue
        svg = SVG_DIR / f"{stem}.svg"
        if not svg.exists():
            skipped.append(f"{name} (no {stem}.svg)")
            continue

        frames = []
        for size in SIZES:
            rgba = render(svg, size)
            xhot = int(round(hx / VIEWBOX * size))
            yhot = int(round(hy / VIEWBOX * size))
            frames.append((size, size, size, xhot, yhot, 0, rgba))

        (cursors_out / name).write_bytes(xcursor(frames))
        built += 1

        for alias in aliases:
            if alias == name:
                continue
            link = cursors_out / alias
            if link.is_symlink() or link.exists():
                link.unlink()
            link.symlink_to(name)
            links += 1

    (DIST / "index.theme").write_text(
        "[Icon Theme]\nName=cce\nComment=CCE desktop cursors\n"
    )
    (DIST / "cursor.theme").write_text("[Icon Theme]\nName=cce\nInherits=cce\n")

    print(f"built {built} cursors x {len(SIZES)} sizes, {links} aliases -> {DIST}")
    if skipped:
        print("skipped (source missing): " + ", ".join(skipped))

    if args.install:
        data = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
        target = Path(data) / "icons" / "cce"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(DIST, target, symlinks=True)
        print(f"installed -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
