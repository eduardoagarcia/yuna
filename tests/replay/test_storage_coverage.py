"""Additional tests for storage.py coverage of legacy format."""

import gzip
import json
import tempfile
from pathlib import Path

from faker import Faker

from yuna.replay.storage import GameRecording

fake = Faker()


def test_load_legacy_delta_format() -> None:
    """Test loading incremental recording with legacy delta format."""
    entity_id = fake.uuid4()

    legacy_data = {
        "metadata": {"seed": 42},
        "snapshots": [],
        "incremental": {
            "metadata": {"game": "test"},
            "keyframe_interval": 60,
            "keyframes": {
                "0": {
                    "tick": 0,
                    "timestamp": 0.0,
                    "entities": {entity_id: {"Position": {"x": 0, "y": 0}}},
                    "metadata": {},
                }
            },
            "deltas": {
                "1": {
                    "tick": 1,
                    "added_entities": {},
                    "removed_entities": [],
                    "modified_components": {entity_id: {"Position": {"x": 1, "y": 1}}},
                }
            },
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "legacy.gz"
        with gzip.open(path, mode="wt", encoding="utf-8") as file:
            json.dump(obj=legacy_data, fp=file)

        recording = GameRecording.from_file(path=path)

        assert recording.incremental is not None
        assert 0 in recording.incremental.keyframes
        assert 1 in recording.incremental.deltas

        delta = recording.incremental.deltas[1]
        assert delta.tick == 1
        assert len(delta.components.modified) == 1


def test_load_legacy_delta_format_with_entity_changes() -> None:
    """Test loading legacy format with added/removed entities."""
    entity_id1 = fake.uuid4()
    entity_id2 = fake.uuid4()
    entity_id3 = fake.uuid4()

    legacy_data = {
        "metadata": {"seed": 42},
        "snapshots": [],
        "incremental": {
            "metadata": {"game": "test"},
            "keyframe_interval": 60,
            "keyframes": {
                "0": {
                    "tick": 0,
                    "timestamp": 0.0,
                    "entities": {entity_id1: {"Health": {"value": 100}}},
                    "metadata": {},
                }
            },
            "deltas": {
                "1": {
                    "tick": 1,
                    "added_entities": {entity_id2: {"Speed": {"value": 5}}},
                    "removed_entities": [entity_id1],
                    "modified_components": {
                        entity_id3: {"Position": {"x": 10, "y": 10}}
                    },
                }
            },
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "legacy_entity_changes.gz"
        with gzip.open(path, mode="wt", encoding="utf-8") as file:
            json.dump(obj=legacy_data, fp=file)

        recording = GameRecording.from_file(path=path)

        assert recording.incremental is not None
        delta = recording.incremental.deltas[1]
        assert delta.tick == 1
        assert len(delta.entities.added) == 1
        assert entity_id2 in delta.entities.added
        assert len(delta.entities.removed) == 1
        assert entity_id1 in delta.entities.removed
        assert len(delta.components.modified) == 1
        assert entity_id3 in delta.components.modified
