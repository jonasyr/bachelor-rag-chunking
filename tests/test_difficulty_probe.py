import importlib.util

from config import PILOT_DIR, ROOT


def load_probe():
    spec = importlib.util.spec_from_file_location(
        "difficulty_probe", ROOT / "scripts" / "difficulty_probe.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_pilot_set_comes_from_the_config():
    assert load_probe().pilot_dir(["difficulty_probe.py"]) == PILOT_DIR


def test_a_named_pilot_set_is_resolved_from_the_repo_root():
    probe = load_probe()
    assert probe.pilot_dir(["difficulty_probe.py", "data/pilot/hard"]) == ROOT / "data/pilot/hard"
