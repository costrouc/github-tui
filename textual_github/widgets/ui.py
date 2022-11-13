from typing import Any

from textual.message import Message, MessageTarget
from textual import events, log
from textual.widgets import DataTable, Input


class SelectableDataTable(DataTable):
    DEFAULT_CSS = '''
    SelectableDataTable {
      height: auto;
    }
    '''

    class Selected(Message):
        """Element selected message."""

        def __init__(self, sender: MessageTarget, value: Any) -> None:
            self.value = value
            super().__init__(sender)

    def get_current_selected(self):
        raise NotImplementedError()

    async def on_click(self, event: events.Click) -> None:
        await self.emit(self.Selected(self, self.get_current_selected()))

    async def key_enter(self, event: events.Key) -> None:
        await self.emit(self.Selected(self, self.get_current_selected()))

    def on_key(self, event: events.Key):
        # adding emacs keybindings
        if event.key == "ctrl+n":
            self.key_down(event)
        elif event.key == "ctrl+p":
            self.key_up(event)
        elif event.key == "ctrl+b":
            self.key_left(event)
        elif event.key == "ctrl+f":
            self.key_right(event)


class EmacsInput(Input):
    def on_key(self, event: events.Key):
        # adding emacs keybindings
        if event.key == "ctrl+a":
            self.action_home()
        elif event.key == "ctrl+e":
            self.action_end()
        elif event.key == "ctrl+b":
            self.action_cursor_left()
        elif event.key == "ctrl+f":
            self.action_cursor_right()
        elif event.key == "ctrl+k":
            self.action_delete_right()
