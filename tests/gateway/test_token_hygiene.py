from gateway.token_hygiene import choose_hygiene_token_count


def test_small_transcript_ignores_implausibly_large_stored_prompt_tokens():
    history = [
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "two"},
        {"role": "user", "content": "three"},
        {"role": "assistant", "content": "four"},
    ]

    decision = choose_hygiene_token_count(
        history,
        stored_prompt_tokens=1_801_438,
        estimate_tokens=lambda messages: 120,
    )

    assert decision.tokens == 120
    assert decision.source == "estimated_stored_implausible"


def test_large_but_plausible_stored_prompt_tokens_are_preserved():
    history = [
        {"role": "user", "content": "x" * 10_000},
        {"role": "assistant", "content": "y" * 10_000},
        {"role": "user", "content": "z" * 10_000},
        {"role": "assistant", "content": "w" * 10_000},
    ]

    decision = choose_hygiene_token_count(
        history,
        stored_prompt_tokens=15_000,
        estimate_tokens=lambda messages: 10_000,
    )

    assert decision.tokens == 15_000
    assert decision.source == "actual"
