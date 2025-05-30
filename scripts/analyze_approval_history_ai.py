import json
from collections import Counter

def summarize_training_log(log_path="data/training_log.jsonl") -> dict:
    results = []
    mismatches = Counter()
    try:
        with open(log_path, "r") as f:
            for line in f:
                entry = json.loads(line)
                results.append(entry)
                for detail in entry.get("details", []):
                    if not detail.get("match"):
                        mismatches[detail["bank"]] += 1
    except FileNotFoundError:
        return {"error": "training_log.jsonl not found"}

    if not results:
        return {"error": "no entries in training log"}

    total_clients = len(results)
    total_accuracy = sum([float(r["accuracy"].strip('%')) for r in results])
    average_accuracy = round(total_accuracy / total_clients, 2)

    most_missed = mismatches.most_common(5)

    return {
        "total_clients": total_clients,
        "average_accuracy": f"{average_accuracy}%",
        "most_common_mismatches": most_missed,
        "latest_clients": [r["client_id"] for r in results[-5:]]
    }
