"""A transport-independent command facade for a CLI, IDE or HTTP handler."""
from mini_pi.streaming import text_of
class AgentRPC:
    def __init__(self, agent):
        self.agent = agent

    def handle(self, request):
        identifier = request.get("id")
        command = request.get("command")
        params = request.get("params", {})
        try:
            if command == "prompt":
                result = self.agent.run(params["text"], params.get("thread_id", "main"), attachments=params.get("attachments",()))
                value = {"paused": bool(result.get("__interrupt__")), "messages": len(result["messages"]), "answer":text_of(result["messages"][-1]) if result['messages'] else '', "interrupts":[item.value for item in result.get('__interrupt__',[])]}
            elif command == "resume":
                result = self.agent.resume(params["approved"], params.get("thread_id", "main"))
                value = {"paused": bool(result.get("__interrupt__")), "messages": len(result["messages"]), "answer":text_of(result["messages"][-1]) if result['messages'] else '', "interrupts":[item.value for item in result.get('__interrupt__',[])]}
            elif command in {"steer", "followup"}:
                self.agent.control.enqueue(params["text"], command)
                value = {"queued": True}
            elif command == "cancel":
                self.agent.control.cancel()
                value = {"cancelled": True}
            elif command == "fork":
                self.agent.fork(params["leaf"], params["thread_id"])
                value = {"created": True}
            else:
                raise ValueError("未知命令")
            return {"id": identifier, "ok": True, "result": value}
        except Exception as error:
            return {"id": identifier, "ok": False, "error": f"{type(error).__name__}: {error}"}
