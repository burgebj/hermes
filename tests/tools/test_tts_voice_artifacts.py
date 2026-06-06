import json
import subprocess
from pathlib import Path

from tools import tts_tool


def _completed(stdout: str):
    return subprocess.CompletedProcess(
        args=["ffprobe"],
        returncode=0,
        stdout=stdout,
        stderr="",
    )


def test_mp3_payload_named_ogg_is_not_telegram_voice(monkeypatch, tmp_path):
    path = tmp_path / "reply.ogg"
    path.write_bytes(b"fake")

    validator = getattr(tts_tool, "_is_telegram_voice_artifact", None)
    assert callable(validator)

    monkeypatch.setattr(
        tts_tool.subprocess,
        "run",
        lambda *args, **kwargs: _completed(json.dumps({
            "format": {"format_name": "mp3"},
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "duration": "1.2",
                }
            ],
        })),
    )

    assert validator(str(path)) is False


def test_ogg_opus_payload_is_telegram_voice(monkeypatch, tmp_path):
    path = tmp_path / "reply.ogg"
    path.write_bytes(b"fake")

    validator = getattr(tts_tool, "_is_telegram_voice_artifact", None)
    assert callable(validator)

    monkeypatch.setattr(
        tts_tool.subprocess,
        "run",
        lambda *args, **kwargs: _completed(json.dumps({
            "format": {"format_name": "ogg"},
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "opus",
                    "duration": "1.2",
                }
            ],
        })),
    )

    assert validator(str(path)) is True


def test_edge_requested_ogg_generates_native_mp3_then_validated_voice(
    monkeypatch,
    tmp_path,
):
    requested = tmp_path / "reply.ogg"
    generated_paths = []

    async def fake_generate_edge(text, output_path, config):
        generated_paths.append(Path(output_path))
        Path(output_path).write_bytes(b"mp3-bytes")
        return output_path

    def fake_convert(path):
        converted = tmp_path / "reply.voice.ogg"
        converted.write_bytes(b"ogg-opus")
        return str(converted)

    monkeypatch.setenv("HERMES_SESSION_PLATFORM", "telegram")
    monkeypatch.setattr(tts_tool, "_load_tts_config", lambda: {"provider": "edge"})
    monkeypatch.setattr(tts_tool, "_import_edge_tts", lambda: object())
    monkeypatch.setattr(tts_tool, "_generate_edge_tts", fake_generate_edge)
    monkeypatch.setattr(tts_tool, "_convert_to_opus", fake_convert)
    monkeypatch.setattr(
        tts_tool,
        "_is_telegram_voice_artifact",
        lambda path: Path(path).name == "reply.voice.ogg",
        raising=False,
    )

    data = json.loads(tts_tool.text_to_speech_tool(text="hello", output_path=str(requested)))

    assert data["success"] is True
    assert data["voice_compatible"] is True
    assert data["file_path"] == str(tmp_path / "reply.voice.ogg")
    assert data["media_tag"] == f"[[audio_as_voice]]\nMEDIA:{tmp_path / 'reply.voice.ogg'}"
    assert generated_paths == [tmp_path / "reply.mp3"]


def test_convert_to_opus_uses_distinct_validated_voice_artifact(monkeypatch, tmp_path):
    source = tmp_path / "reply.ogg"
    source.write_bytes(b"mp3-bytes")
    captured = {}

    def fake_run(args, *unused_args, **unused_kwargs):
        target = Path(args[-2])
        captured["source"] = args[2]
        captured["target"] = str(target)
        target.write_bytes(b"ogg-opus")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(tts_tool, "_has_ffmpeg", lambda: True)
    monkeypatch.setattr(tts_tool.subprocess, "run", fake_run)
    monkeypatch.setattr(
        tts_tool,
        "_is_telegram_voice_artifact",
        lambda path: Path(path).name == "reply.voice.ogg",
        raising=False,
    )

    result = tts_tool._convert_to_opus(str(source))

    assert result == str(tmp_path / "reply.voice.ogg")
    assert captured == {
        "source": str(source),
        "target": str(tmp_path / "reply.voice.ogg"),
    }
