from importlib import reload


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "XYZ")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    monkeypatch.setenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    from app import config
    reload(config)

    assert config.settings.api_key == "XYZ"
    assert config.settings.base_url == "https://api.siliconflow.cn/v1"
    assert config.settings.model == "Qwen/Qwen2.5-7B-Instruct"


def test_build_llm_uses_settings(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "XYZ")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    monkeypatch.setenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    from app import config as config_mod
    reload(config_mod)
    from app.ai import llm as llm_mod
    reload(llm_mod)

    llm = llm_mod.build_llm()
    assert str(llm.openai_api_base).rstrip("/").endswith("/v1")
    assert llm.model_name == "Qwen/Qwen2.5-7B-Instruct"


def test_personas_non_empty():
    from app.ai.personas import PERSONAS, random_persona

    assert len(PERSONAS) >= 6
    persona = random_persona(seed=1)
    assert persona.name and persona.style


def test_role_system_prompt_contains_role():
    from app.ai.personas import Persona
    from app.ai.prompts import build_system_prompt
    from app.game.constants import Role

    persona = Persona(name="A", style="calm")
    prompt = build_system_prompt(role=Role.SEER, persona=persona, wolf_teammates=[])
    assert "预言家" in prompt or "seer" in prompt.lower()
    assert "calm" in prompt.lower() or "A" in prompt
