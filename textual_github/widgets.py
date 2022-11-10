from textual.reactive import reactive
from rich.markdown import Markdown

from textual.message import Message, MessageTarget
from textual.widgets import Static


class GithubComment(Static):
    DEFAULT_CSS = """
    GithubComment {
        border: tall grey;
        margin: 1;
    }
    """

    class Selected(Message):
        """Element selected message."""

        def __init__(self, sender: MessageTarget) -> None:
            self.sender = sender
            super().__init__(sender)

    ACTIVE_COLOR = "orange"
    INACTIVE_COLOR = "grey"

    comment = reactive("Edit (click and press \"e\")", layout=True)
    editable = reactive(True)
    active = reactive(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.comment = "Edit (click and press \"e\")"

    def watch_active(self, old_active: bool, new_active: bool):
        if self.active:
            self.styles.border = ("tall", self.ACTIVE_COLOR)
        else:
            self.styles.border = ("tall", self.INACTIVE_COLOR)

    def render(self):
        return Markdown(self.comment)

    async def on_click(self) -> None:
        if self.editable:
            await self.emit(self.Selected(self))
