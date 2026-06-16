"""Tests for the ``{video}`` / ``{audio}`` directives in ``media.py``."""

from __future__ import annotations

from projecter.media import (
    _mime,
    _parse_body,
    _youtube_id,
    _youtube_start_seconds,
    protect_media,
    restore_media,
)


# --- helpers --------------------------------------------------------------


def test_mime_known_and_unknown() -> None:
    from projecter.media import _AUDIO_MIME, _VIDEO_MIME

    assert _mime("clip.MP4", _VIDEO_MIME) == "video/mp4"
    assert _mime("song.m4a", _AUDIO_MIME) == "audio/mp4"
    assert _mime("noext", _VIDEO_MIME) == ""
    assert _mime("file.xyz", _VIDEO_MIME) == ""


def test_youtube_id_forms() -> None:
    assert _youtube_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _youtube_id("https://youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _youtube_id("https://youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _youtube_id("static/videos/demo.mp4") is None


def test_youtube_start_seconds() -> None:
    assert _youtube_start_seconds("u?t=90") == 90
    assert _youtube_start_seconds("u?t=1m30s") == 90
    assert _youtube_start_seconds("u?t=1h2m3s") == 3723
    assert _youtube_start_seconds("u?start=45") == 45
    assert _youtube_start_seconds("u") == 0


def test_parse_body_options_flags_and_caption() -> None:
    options, flags, caption = _parse_body(
        ":width: 80%\n:autoplay:\n\nA caption line.\n"
    )
    assert options == {"width": "80%"}
    assert flags == {"autoplay"}
    assert caption == "A caption line."


def test_parse_body_caption_starts_at_first_non_option() -> None:
    options, flags, caption = _parse_body(":loop:\nImmediate caption.")
    assert flags == {"loop"}
    assert caption == "Immediate caption."


# --- video ----------------------------------------------------------------


def test_video_static_file() -> None:
    md = (
        "```{video} static/videos/demo.mp4\n"
        ":width: 80%\n:poster: thumb.png\n:autoplay:\n:loop:\n"
        "\nA demo clip.\n```\n"
    )
    protected, blocks = protect_media(md)
    assert "MEDIAPLACEHOLDER" in protected
    html = blocks[0]
    assert "<video" in html and 'class="media-video"' in html
    assert 'type="video/mp4"' in html
    assert "width:80%" in html and 'poster="thumb.png"' in html
    assert " autoplay" in html and " loop" in html
    assert "<figcaption>A demo clip.</figcaption>" in html


def test_video_static_file_stays_video() -> None:
    _, blocks = protect_media("```{video} static/v.mp4\n```\n")
    assert "<video" in blocks[0] and "<iframe" not in blocks[0]
    assert 'type="video/mp4"' in blocks[0]


def test_video_unknown_extension_omits_type() -> None:
    _, blocks = protect_media("```{video} static/v.mov\n```\n")
    assert "type=" not in blocks[0]


def test_video_youtube_embed() -> None:
    md = "```{video} https://youtu.be/dQw4w9WgXcQ?t=1m30s\n:muted:\n\nA clip.\n```\n"
    _, blocks = protect_media(md)
    html = blocks[0]
    assert "<iframe" in html and "<video" not in html
    assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in html
    assert "start=90" in html and "mute=1" in html
    assert "<figcaption>A clip.</figcaption>" in html


def test_video_youtube_loop_adds_playlist() -> None:
    md = "```{video} https://youtu.be/dQw4w9WgXcQ\n:loop:\n```\n"
    _, blocks = protect_media(md)
    assert "loop=1&amp;playlist=dQw4w9WgXcQ" in blocks[0]


# --- audio ----------------------------------------------------------------


def test_audio_player_with_label() -> None:
    md = "```{audio} static/audio/podcast.m4a\n:label: fig-podcast\n\nThe podcast.\n```\n"
    _, blocks = protect_media(md)
    html = blocks[0]
    assert "<audio controls" in html
    assert 'type="audio/mp4"' in html
    assert 'id="fig-podcast"' in html
    assert "<figcaption>The podcast.</figcaption>" in html


def test_audio_escapes_caption_html() -> None:
    md = "```{audio} a.mp3\n\nTom & <b>Jerry</b>\n```\n"
    _, blocks = protect_media(md)
    assert "Tom &amp; &lt;b&gt;Jerry&lt;/b&gt;" in blocks[0]


# --- protect / restore ----------------------------------------------------


def test_protect_media_no_directive_is_noop() -> None:
    protected, blocks = protect_media("Just plain text.\n")
    assert blocks == []
    assert protected == "Just plain text.\n"


def test_multiple_media_blocks_indexed() -> None:
    md = "```{audio} a.mp3\n```\n\n```{audio} b.mp3\n```\n"
    protected, blocks = protect_media(md)
    assert len(blocks) == 2
    assert "MEDIAPLACEHOLDER0MEDIA" in protected
    assert "MEDIAPLACEHOLDER1MEDIA" in protected


def test_restore_media_unwraps_paragraph() -> None:
    _, blocks = protect_media("```{audio} a.mp3\n```\n")
    out = restore_media("<p>MEDIAPLACEHOLDER0MEDIA</p>", blocks)
    assert out == blocks[0]
    assert "MEDIAPLACEHOLDER" not in out
