"""Convert ``{video}`` and ``{audio}`` directives into HTML media players.

MyST renders ``{figure}`` natively, but there is no built-in directive for
audio/video. Rather than register custom docutils directives, we use the same
two-phase strategy as :mod:`projecter.latex`:

* :func:`protect_media` pulls the fenced ``{video}`` / ``{audio}`` blocks out of
  the markdown and leaves a plain-text placeholder (before MyST rendering).
* :func:`restore_media` swaps the rendered HTML players back in afterwards.

A block looks like a fenced MyST directive::

    ```{video} static/videos/demo.mp4
    :poster: static/images/thumb.png
    :width: 80%
    :autoplay:
    :loop:
    :muted:

    An optional caption rendered beneath the player.
    ```

    ```{audio} static/audio/podcast.m4a
    :label: fig-podcast

    AI-generated podcast (paper introduction).
    ```
"""

from __future__ import annotations

import html
import re

# A fenced ``{video}`` / ``{audio}`` directive: the opening fence captures the
# kind and the source argument, the body holds ``:option:`` lines and a caption.
_MEDIA_RE = re.compile(
    r"^```\{(video|audio)\}[ \t]*(.*?)[ \t]*\n(.*?)^```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)
_OPTION_RE = re.compile(r"^:([\w-]+):[ \t]*(.*?)[ \t]*$")

_PLACEHOLDER = "MEDIAPLACEHOLDER{}MEDIA"

# Map file extensions to MIME types for the <source> element.
_VIDEO_MIME = {".mp4": "video/mp4", ".webm": "video/webm", ".ogv": "video/ogg"}
_AUDIO_MIME = {
    ".m4a": "audio/mp4", ".mp3": "audio/mpeg", ".wav": "audio/wav",
    ".ogg": "audio/ogg", ".oga": "audio/ogg", ".aac": "audio/aac",
    ".flac": "audio/flac",
}

# Options that are flags (presence-only, no value) for each kind.
_VIDEO_FLAGS = {"autoplay", "loop", "muted", "playsinline"}
_AUDIO_FLAGS: set[str] = set()

# YouTube URL forms: watch?v=, youtu.be/, embed/, shorts/. Captures the 11-char
# video id.
_YOUTUBE_RE = re.compile(
    r"(?:youtube(?:-nocookie)?\.com/(?:watch\?(?:[^ ]*&)?v=|embed/|shorts/)"
    r"|youtu\.be/)([\w-]{11})"
)
# A start time on the URL, as `t=` or `start=`, e.g. `90`, `90s` or `1m30s`.
_YT_START_RE = re.compile(r"[?&#](?:t|start)=(\d+h)?(\d+m)?(\d+s?)?")


def _mime(src: str, table: dict[str, str]) -> str:
    ext = "." + src.rsplit(".", 1)[-1].lower() if "." in src else ""
    return table.get(ext, "")


def _youtube_id(src: str) -> str | None:
    """Return the YouTube video id if ``src`` is a YouTube URL, else ``None``."""
    match = _YOUTUBE_RE.search(src)
    return match.group(1) if match else None


def _youtube_start_seconds(src: str) -> int:
    """Parse a `t=`/`start=` offset on a YouTube URL into whole seconds."""
    match = _YT_START_RE.search(src)
    if not match:
        return 0
    hours, minutes, seconds = match.groups()
    total = 0
    if hours:
        total += int(hours[:-1]) * 3600
    if minutes:
        total += int(minutes[:-1]) * 60
    if seconds:
        total += int(seconds.rstrip("s"))
    return total


def _parse_body(body: str) -> tuple[dict[str, str], set[str], str]:
    """Split a directive body into ``:key: value`` options and a caption."""
    options: dict[str, str] = {}
    flags: set[str] = set()
    caption_lines: list[str] = []
    in_caption = False
    for line in body.splitlines():
        if in_caption:
            caption_lines.append(line)
            continue
        match = _OPTION_RE.match(line)
        if match:
            key, value = match.group(1).lower(), match.group(2)
            if value:
                options[key] = value
            else:
                flags.add(key)
        elif line.strip() == "":
            in_caption = True  # blank line ends the option block
        else:
            # A non-option, non-blank line starts the caption immediately.
            in_caption = True
            caption_lines.append(line)
    return options, flags, "\n".join(caption_lines).strip()


def _figure(player: str, options: dict[str, str], caption: str) -> str:
    """Wrap a media player in a ``<figure>`` with an optional caption/label."""
    attr = f' id="{html.escape(options["label"], quote=True)}"' if "label" in options else ""
    cap = f"<figcaption>{html.escape(caption)}</figcaption>" if caption else ""
    return f'<figure class="media-figure"{attr}>{player}{cap}</figure>'


def _youtube_html(
    video_id: str, src: str, options: dict[str, str], flags: set[str], caption: str
) -> str:
    """Render a responsive YouTube embed inside the media figure."""
    params: list[str] = []
    if _youtube_start_seconds(src):
        params.append(f"start={_youtube_start_seconds(src)}")
    if "autoplay" in flags:
        params.append("autoplay=1")
    if "muted" in flags:
        params.append("mute=1")
    if "loop" in flags:
        # YouTube needs an explicit playlist for a single video to loop.
        params.append(f"loop=1&playlist={video_id}")
    query = ("?" + "&".join(params)) if params else ""
    url = html.escape(f"https://www.youtube-nocookie.com/embed/{video_id}{query}", quote=True)
    style = (
        f' style="width:{html.escape(options["width"], quote=True)}"'
        if "width" in options
        else ""
    )
    player = (
        f'<div class="media-embed"{style}>'
        f'<iframe src="{url}" title="{html.escape(options.get("title", "YouTube video"), quote=True)}" '
        'frameborder="0" loading="lazy" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
        'gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>'
        "</div>"
    )
    return _figure(player, options, caption)


def _video_html(src: str, options: dict[str, str], flags: set[str], caption: str) -> str:
    video_id = _youtube_id(src)
    if video_id:
        return _youtube_html(video_id, src, options, flags, caption)
    src = html.escape(src, quote=True)
    attrs = ["controls", 'class="media-video"']
    if "width" in options:
        attrs.append(f'style="width:{html.escape(options["width"], quote=True)}"')
    if "poster" in options:
        attrs.append(f'poster="{html.escape(options["poster"], quote=True)}"')
    for flag in _VIDEO_FLAGS & flags:
        attrs.append(flag)
    mime = _mime(src, _VIDEO_MIME)
    type_attr = f' type="{mime}"' if mime else ""
    player = (
        f"<video {' '.join(attrs)}>"
        f'<source src="{src}"{type_attr}>'
        "Your browser does not support the video tag."
        "</video>"
    )
    return _figure(player, options, caption)


def _audio_html(src: str, options: dict[str, str], flags: set[str], caption: str) -> str:
    src = html.escape(src, quote=True)
    mime = _mime(src, _AUDIO_MIME)
    type_attr = f' type="{mime}"' if mime else ""
    player = (
        '<audio controls class="media-audio">'
        f'<source src="{src}"{type_attr}>'
        "Your browser does not support the audio element."
        "</audio>"
    )
    return _figure(player, options, caption)


def _block_to_html(kind: str, src: str, body: str) -> str:
    options, flags, caption = _parse_body(body)
    if kind == "video":
        return _video_html(src, options, flags, caption)
    return _audio_html(src, options, flags, caption)


def protect_media(text: str) -> tuple[str, list[str]]:
    """Replace ``{video}`` / ``{audio}`` directives with placeholders."""
    blocks: list[str] = []

    def repl(match: re.Match[str]) -> str:
        blocks.append(_block_to_html(match.group(1), match.group(2), match.group(3)))
        return f"\n\n{_PLACEHOLDER.format(len(blocks) - 1)}\n\n"

    return _MEDIA_RE.sub(repl, text), blocks


def restore_media(html_text: str, blocks: list[str]) -> str:
    """Swap rendered placeholders back for their media players."""
    for i, block in enumerate(blocks):
        token = _PLACEHOLDER.format(i)
        html_text = html_text.replace(f"<p>{token}</p>", block).replace(token, block)
    return html_text
