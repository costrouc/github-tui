import tempfile
import subprocess
import os

from github import Github
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual import events
from textual.containers import Container
from textual.widgets import Footer, Header, Static, DataTable

from textual_github.widgets import GithubComment


github_client = Github(os.environ['GITHUB_API_TOKEN'])

CURRENT_USER = github_client.get_user()


class GithubApp(App):
    """A working 'desktop' github application."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("e", "edit", "Edit"),
    ]

    CURRENT_SELECTED = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        table = DataTable()
        table.add_columns('a', 'b', 'c', 'd')
        table.add_rows([
            ["e", "f", "g", "h"]
        ])

        comments = [
            GithubComment(),
            GithubComment(),
            GithubComment()
        ]
        comments[1].editable = False

        yield Header()
        yield Container(
            Static(CURRENT_USER.name, id="user"),
            *comments
        )
        yield table
        yield Footer()

    def on_github_comment_selected(self, message: GithubComment.Selected) -> None:
        if self.CURRENT_SELECTED is not None:
            self.CURRENT_SELECTED.active = False
        self.CURRENT_SELECTED = message.sender
        self.CURRENT_SELECTED.active = True

    async def action_edit(self) -> None:
        if self.CURRENT_SELECTED:
            self._driver.stop_application_mode()
            with tempfile.NamedTemporaryFile() as tempf:
                with open(tempf.name, "w") as f:
                    f.write(self.CURRENT_SELECTED.comment)

                subprocess.run(f"$EDITOR {tempf.name}", shell=True)

                with open(tempf.name) as f:
                    self.CURRENT_SELECTED.comment = f.read()
            self._driver.start_application_mode()
