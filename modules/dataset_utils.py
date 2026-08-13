import json
from pathlib import Path


def load_voice_dataset(split="train"):
    """
    Load the TeleAntiFraud dataset JSON file.

    Args:
        split: "train" or "test"

    Returns:
        List of simplified dataset records.
    """

    if split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")

    file_path = Path("data") / f"{split}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        raw_data = json.load(file)

    records = []

    for index, item in enumerate(raw_data):
        try:
            content = item["prompt"][1]["content"]

            audio_path = None

            for part in content:
                if part.get("type") == "audio":
                    audio_path = part.get("audio_url")
                    break

            label = item.get("answer", "").strip().lower()

            records.append({
                "id": index,
                "audio_url": audio_path,
                "label": label,
                "is_fraud": label == "fraud"
            })

        except (KeyError, IndexError, TypeError):
            continue

    return records


def get_dataset_summary(split="train"):
    """
    Return a summary of the dataset.
    """

    records = load_voice_dataset(split)

    fraud_count = sum(
        1 for record in records
        if record["label"] == "fraud"
    )

    normal_count = sum(
        1 for record in records
        if record["label"] == "normal"
    )

    return {
        "split": split,
        "total": len(records),
        "fraud": fraud_count,
        "normal": normal_count
    }