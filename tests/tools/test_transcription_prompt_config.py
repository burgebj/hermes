"""Tests for STT prompt configuration support."""

from unittest.mock import MagicMock, patch


def test_openai_transcription_forwards_prompt_and_language_from_config(monkeypatch, tmp_path):
    from tools import transcription_tools as tt

    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"RIFF....WAVEfmt ")

    monkeypatch.setattr(
        tt,
        "_load_stt_config",
        lambda: {
            "openai": {
                "api_key": "sk-local",
                "base_url": "http://speaches.test/v1",
                "prompt": "Transcris CLI comme CLI en contexte informatique.",
                "language": "fr",
            }
        },
    )

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = MagicMock(text="ok")

    with patch.object(tt, "_HAS_OPENAI", True), patch("openai.OpenAI", return_value=mock_client):
        result = tt._transcribe_openai(str(audio), "Systran/faster-whisper-large-v3")

    assert result["success"] is True
    kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
    assert kwargs["prompt"] == "Transcris CLI comme CLI en contexte informatique."
    assert kwargs["language"] == "fr"


def test_openai_transcription_reads_prompt_from_configured_file(monkeypatch, tmp_path):
    from tools import transcription_tools as tt

    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"RIFF....WAVEfmt ")
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Prompt depuis fichier.\n", encoding="utf-8")

    monkeypatch.setattr(
        tt,
        "_load_stt_config",
        lambda: {
            "openai": {
                "api_key": "sk-local",
                "base_url": "http://speaches.test/v1",
                "prompt_file": str(prompt_file),
            }
        },
    )

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = {"text": "ok"}

    with patch.object(tt, "_HAS_OPENAI", True), patch("openai.OpenAI", return_value=mock_client):
        result = tt._transcribe_openai(str(audio), "Systran/faster-whisper-large-v3")

    assert result["success"] is True
    kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
    assert kwargs["prompt"] == "Prompt depuis fichier."


def test_inline_prompt_takes_precedence_over_prompt_file(monkeypatch, tmp_path):
    from tools import transcription_tools as tt

    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("file prompt", encoding="utf-8")

    monkeypatch.setattr(
        tt,
        "_load_stt_config",
        lambda: {"openai": {"prompt": "inline prompt", "prompt_file": str(prompt_file)}},
    )

    assert tt._get_openai_stt_prompt() == "inline prompt"
