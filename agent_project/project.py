from mini_pi.app import MiniPi
from mini_pi.events import EventDecoder, encode_event


def build_project(root, data, model=None, on_event=lambda event: None):
    decoder = EventDecoder()

    def display(event):
        for item in decoder.feed(encode_event(event)):
            on_event(item)

    return MiniPi(
        root=root,
        data=data,
        model=model,
        on_event=display,
        approve=True,
        context_mode="window",
    )
