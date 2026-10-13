"""Run a B-only terminal demo. Defaults to offline; never sends messages."""
import argparse
import json
from pathlib import Path
from agents.classifier import classify_message
from agents.reply_generator import generate_reply


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("mock", "llm"), default="mock")
    parser.add_argument("--message", help="Optional synthetic work message to analyse")
    args = parser.parse_args()
    if args.message is not None:
        messages = [{"id": "custom", "message": args.message}]
    else:
        path = Path(__file__).parent / "data" / "agent_test_cases.json"
        messages = json.loads(path.read_text(encoding="utf-8"))
    print("Mode:", args.mode, "| draft only | no messages are sent")
    for case in messages:
        message = {key: value for key, value in case.items() if key != "expected_category"}
        result = classify_message(message, mode=args.mode)
        reply = generate_reply(message, result)
        print(json.dumps({**result, "suggested_reply": reply["suggested_reply"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
