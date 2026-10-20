"""Tutor regressions using a fake OpenAI client; no credentials or network."""
from types import SimpleNamespace

import openai
import pytest
from pydantic import ValidationError

from app.api.tutor import TutorRequest
from app.services import tutor


def test_tutor_keeps_recent_conversation_and_phase_context(monkeypatch):
    calls = []
    monkeypatch.setattr(tutor, "get_settings", lambda: SimpleNamespace(
        ai_provider="openai", openai_api_key="synthetic-test-only", tutor_model="test-model", tutor_vision_enabled=True))
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_text="Hãy so sánh bằng chứng của bạn.")
    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(create=create)))
    conversation = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"Turn {i}"} for i in range(12)]
    provider, blocks = tutor.grounded_tutor_blocks(
        language="vi", message="Giải thích rõ hơn gợi ý vừa rồi", retrieved=[], phase="WORK",
        learner_context={"goal": "Mục tiêu đã lưu", "readiness": 0.5,
                         "organize_map": {"synthesis": "Sơ đồ của tôi"}}, conversation=conversation)
    assert provider == "openai" and blocks[0]["content"].startswith("Hãy so sánh")
    sent = calls[0]["input"]
    assert sent[:-1] == conversation[-8:]
    prompt = sent[-1]["content"][0]["text"]
    for required in ("Mục tiêu đã lưu", "Sơ đồ của tôi", "Giải thích rõ hơn gợi ý vừa rồi", "POWER PHASE: WORK", "khái niệm yếu"):
        assert required in prompt


def test_tutor_without_history_preserves_image_input(monkeypatch):
    calls = []
    monkeypatch.setattr(tutor, "get_settings", lambda: SimpleNamespace(
        ai_provider="openai", openai_api_key="synthetic-test-only", tutor_model="test", tutor_vision_enabled=True))
    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: SimpleNamespace(
        responses=SimpleNamespace(create=lambda **kwargs: (calls.append(kwargs) or SimpleNamespace(output_text="Image hint")))))
    tutor.grounded_tutor_blocks(language="en", message="Help with this image", retrieved=[],
                               image_data_url="data:image/png;base64,dGVzdA==")
    assert len(calls[0]["input"]) == 1
    assert calls[0]["input"][0]["content"][1]["type"] == "input_image"


@pytest.mark.parametrize("conversation", [
    [{"role": "system", "content": "untrusted instructions"}],
    [{"role": "user", "content": "x"}] * 9,
    [{"role": "assistant", "content": "x" * 4001}],
])
def test_conversation_rejects_privileged_roles_and_oversized_history(conversation):
    with pytest.raises(ValidationError):
        TutorRequest(message="Question", conversation=conversation)


def test_old_clients_need_not_send_conversation():
    assert TutorRequest(message="Question").conversation == []
