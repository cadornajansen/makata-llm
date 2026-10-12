"""Reproduce the published tokenizer fixture without downloading model weights.

Requires tokenizers==0.23.3. Run from any directory; this check never edits the fixture.
"""
import json
from pathlib import Path
from urllib.request import urlopen

from tokenizers import Tokenizer


def main() -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "lib/research/tokenization.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    url = f"https://huggingface.co/{fixture['model']}/resolve/{fixture['revision']}/tokenizer.json"
    with urlopen(url, timeout=60) as response:
        tokenizer = Tokenizer.from_str(response.read().decode("utf-8"))
    for example in fixture["examples"]:
        encoded = tokenizer.encode(example["text"], add_special_tokens=False)
        assert encoded.ids == example["ids"], example["language"]
        assert tokenizer.decode(encoded.ids) == example["text"], example["language"]
        assert [tokenizer.decode([token_id]) for token_id in encoded.ids] == example["pieces"]
        print(f"{example['language']}: {len(encoded.ids)} tokens verified")


if __name__ == "__main__":
    main()
