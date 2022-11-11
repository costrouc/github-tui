from typing import List

from github.Repository import Repository
from github.NamedUser import NamedUser
from github.Issue import Issue
from github.IssueComment import IssueComment

from textual.reactive import reactive
from rich.markdown import Markdown

from textual import events
from textual.app import ComposeResult
from textual.message import Message, MessageTarget
from textual.widgets import Static, DataTable
from textual.widget import Widget
from textual.containers import Vertical, Horizontal, Container


class GithubProfile(Widget):
    def __init__(self, user: NamedUser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user

    def compose(self) -> ComposeResult:
        yield Static(Markdown(f"""
# {self._user.name}

 - company {self._user.company}
 - email {self._user.email}

```{self._user.bio}```
"""))


class GithubRepositories(DataTable):
    class Selected(Message):
        """Element selected message."""

        def __init__(self, sender: MessageTarget, repository: Repository) -> None:
            self.repository = repository
            super().__init__(sender)

    def __init__(self, respositories: List[Repository], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._repositories = respositories

        self.add_columns("owner", "name", "public", "stars")
        for repository in self._repositories:
            self.add_row(
                repository.full_name,
                repository.name,
                str(not repository.private),
                str(repository.stargazers_count)
            )

    async def on_click(self, event: events.Click) -> None:
        super().on_click(event)
        repository = self._repositories[self.cursor_cell.row]
        await self.emit(self.Selected(self, repository))


class GithubRepository(Widget):
    def __init__(self, repository: Repository, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._repository = repository
        self._issues = repository.get_issues()

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static(self._repository.full_name),
            Static(str(self._repository.stargazers_count)),
            Static(str(self._repository.open_issues)),
            GithubIssues(self._issues)
        )

class GithubIssues(DataTable):
    class Selected(Message):
        """Element selected message."""

        def __init__(self, sender: MessageTarget, issue: Issue) -> None:
            self.issue = issue
            super().__init__(sender)

    def __init__(self, issues: List[Issue], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._issues = issues

        self.add_columns("number", "title")
        for issue in self._issues:
            self.add_row(str(issue.number), issue.title)

    async def on_click(self, event: events.Click) -> None:
        super().on_click(event)
        issue = self._issues[self.cursor_cell.row]
        await self.emit(self.Selected(self, issue))


class GithubIssue(Widget):
    def __init__(self, issue: Issue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._issue = issue
        self._comments = issue.get_comments()

    def compose(self) -> ComposeResult:
        yield Vertical(
            GithubComment(self._issue),
            *[GithubComment(comment) for comment in self._comments]
        )


class GithubComment(Widget):
    class Selected(Message):
        """Element selected message."""

        def __init__(self, sender: MessageTarget) -> None:
            self.sender = sender
            super().__init__(sender)

    comment = reactive("Edit (click and press \"e\")", layout=True)
    editable = reactive(True)
    active = reactive(False)

    def __init__(
        self,
        issue_comment: IssueComment,
        editable: bool = True,
        *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._issue_comment = issue_comment
        self.editable = editable
        self.comment = self._issue_comment.body

    def watch_active(self, old_active: bool, new_active: bool):
        if self.active:
            self._body.add_class("active")
        else:
            self._body.remove_class("active")

    def compose(self) -> ComposeResult:
        self._body = Static(
            Markdown(self._issue_comment.body),
        )
        yield Container(
            Vertical(
                Horizontal(
                    Static(f"@{self._issue_comment.user.login}", classes="column"),
                    Static(str(self._issue_comment.created_at), classes="column"),
                ),
                self._body
            )
        )

    def watch_comment(self, comment: str):
        self._body.update(Markdown(comment))

    async def on_click(self) -> None:
        if self.editable:
            await self.emit(self.Selected(self))
