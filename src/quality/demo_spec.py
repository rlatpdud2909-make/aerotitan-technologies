import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def load_spec():
    return json.loads((ROOT / 'data/demo_requirements/DEMO_SPEC_TI64_V1.json').read_text(encoding='utf-8'))
