import argparse

from mini_pi.project import build_project
from mini_pi.streaming import text_of


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="?", default="请解释 hello.py。")
    parser.add_argument("--root", default="workspace")
    parser.add_argument("--data", default=".mini-pi")
    parser.add_argument("--thread", default="main")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--no-stream", action="store_true")
    args = parser.parse_args()

    model = None
    if args.demo:
        from mini_pi.demo import DemoModel
        model = DemoModel()

    def show(event):
        if event["type"] == "text" and not args.no_stream:
            print(event["text"], end="", flush=True)
        elif event["type"] == "tool_start":
            print(f"\n[{event['name']}]")

    agent = build_project(args.root, args.data, model, show)
    try:
        question = args.question
        while True:
            result = agent.run(question, args.thread)
            while result.get("__interrupt__"):
                print(result["__interrupt__"][0].value)
                approved = input("确认执行？[y/N] ").lower() == "y"
                result = agent.resume(approved, args.thread)
            if args.no_stream:
                print(text_of(result["messages"][-1]))
            else:
                print()
            if not args.interactive:
                break
            question = input("> ")
            if question.strip() == "/exit":
                break
    finally:
        agent.close()


if __name__ == "__main__":
    main()
