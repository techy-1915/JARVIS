"""Tests for jarvis.ai – brain, router, and model configs."""


from jarvis.ai.models import DEFAULT_MODEL, MODELS, ModelConfig
from jarvis.ai.router import classify_prompt, get_system_prompt


class TestModelConfig:
    def test_all_required_models_present(self):
        for key in ("phi3", "deepseek-coder", "mistral"):
            assert key in MODELS, f"Model '{key}' missing from MODELS"

    def test_default_model_in_models(self):
        assert DEFAULT_MODEL in MODELS

    def test_model_config_fields(self):
        for key, cfg in MODELS.items():
            assert isinstance(cfg, ModelConfig), f"{key} is not a ModelConfig"
            assert cfg.name, f"{key}.name is empty"
            assert cfg.display_name, f"{key}.display_name is empty"
            assert cfg.context_window > 0, f"{key}.context_window must be positive"
            assert isinstance(cfg.capabilities, list), f"{key}.capabilities must be a list"
            assert 0.0 <= cfg.temperature <= 2.0, f"{key}.temperature out of range"

    def test_coding_model_low_temperature(self):
        """deepseek-coder should use a lower temperature for deterministic output."""
        assert MODELS["deepseek-coder"].temperature < MODELS["phi3"].temperature


class TestRouter:
    def test_code_keywords_route_to_deepseek(self):
        # Each prompt contains >= 2 CODE_KEYWORDS so it routes to deepseek-coder
        prompts = [
            "write a python function to sort a list",       # python + function
            "debug this javascript code",                   # debug + code
            "fix the bug in my python program",             # bug + python
            "refactor this python class method",            # refactor + python + class + method
        ]
        for prompt in prompts:
            result = classify_prompt(prompt)
            assert result == "deepseek-coder", f"Expected deepseek-coder for: {prompt!r}"

    def test_code_block_routes_to_deepseek(self):
        prompt = "What does this code do?\n```python\nprint('hello')\n```"
        assert classify_prompt(prompt) == "deepseek-coder"

    def test_reasoning_keywords_route_to_mistral(self):
        # Each prompt contains >= 2 REASONING_KEYWORDS so it routes to mistral
        prompts = [
            "analyze the pros and cons of this approach",   # analyze + pros and cons
            "compare and evaluate these two approaches",     # compare + evaluate
            "explain the trade-offs and decide which is better",  # explain + trade-offs + decide
        ]
        for prompt in prompts:
            result = classify_prompt(prompt)
            assert result == "mistral", f"Expected mistral for: {prompt!r}"

    def test_general_chat_routes_to_phi3(self):
        prompts = [
            "hello, how are you?",
            "what is the capital of France?",
            "tell me a joke",
        ]
        for prompt in prompts:
            result = classify_prompt(prompt)
            assert result == "phi3", f"Expected phi3 for: {prompt!r}"

    def test_classify_returns_string(self):
        result = classify_prompt("some random text")
        assert isinstance(result, str)

    def test_classify_result_in_known_models(self):
        for prompt in ("write code", "analyze this", "hello"):
            result = classify_prompt(prompt)
            assert result in MODELS, f"Classified to unknown model: {result}"


class TestSystemPrompts:
    def test_all_models_have_system_prompt(self):
        for model in ("phi3", "deepseek-coder", "mistral"):
            prompt = get_system_prompt(model)
            assert isinstance(prompt, str)
            assert len(prompt) > 10, f"System prompt for {model} is too short"

    def test_unknown_model_falls_back_to_phi3(self):
        prompt = get_system_prompt("unknown-model")
        phi3_prompt = get_system_prompt("phi3")
        assert prompt == phi3_prompt

    def test_coding_prompt_mentions_code(self):
        prompt = get_system_prompt("deepseek-coder")
        assert "code" in prompt.lower() or "program" in prompt.lower()

    def test_reasoning_prompt_mentions_analysis(self):
        prompt = get_system_prompt("mistral")
        assert "reason" in prompt.lower() or "analys" in prompt.lower()
