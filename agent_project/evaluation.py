def evaluate_run(events, required_tools, expected_files, actual_files):
    completed = [event.get("name") for event in events if event.get("type") == "tool_end" and event.get("status") == "success"]
    tools_ok = all(name in completed for name in required_tools)
    files_ok = all(actual_files.get(path) == content for path, content in expected_files.items())
    return {"passed": tools_ok and files_ok, "tools_ok": tools_ok, "files_ok": files_ok,
            "model_calls": sum(event.get("type") == "model_end" for event in events)}
