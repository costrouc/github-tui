from typing import List

from github.Repository import Repository
from github.NamedUser import NamedUser
from github.Issue import Issue
from github.IssueComment import IssueComment
from github.Notification import Notification

from textual.reactive import reactive
from rich.markdown import Markdown

from textual import events
from textual.app import ComposeResult
from textual.message import Message, MessageTarget
from textual.widgets import Static
from textual.widget import Widget
from textual.containers import Vertical, Horizontal, Container

from textual_github.widgets.ui import SelectableDataTable


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


class GithubRepositories(SelectableDataTable):
    repositories = reactive([], layout=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_columns("owner", "name", "description", "public", "stars")

    def watch_repositories(self, repositories: List[Repository]):
        self.clear()
        for repository in repositories:
            self.add_row(
                repository.full_name,
                repository.name,
                (repository.description or "")[:32],
                str(not repository.private),
                str(repository.stargazers_count)
            )

    def get_current_selected(self):
        return self.repositories[self.cursor_cell.row]


class GithubRepository(Widget):
    def __init__(self, repository: Repository, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._repository = repository
        self._issues = repository.get_issues()

    def compose(self) -> ComposeResult:
        self._github_issues = GithubIssues()
        self._github_issues.issues = self._issues

        yield Vertical(
            Static(self._repository.full_name),
            Static(str(self._repository.stargazers_count)),
            Static(str(self._repository.open_issues)),
            self._github_issues,
        )

class GithubIssues(SelectableDataTable):
    issues = reactive([], layout=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_columns("number", "title")

    def watch_issues(self, issues: List[Issue]):
        for issue in self.issues:
            self.add_row(str(issue.number), issue.title)

    def get_current_selected(self):
        return self.issues[self.cursor_cell.row]


class GithubIssue(Widget):
    def __init__(self, issue: Issue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._issue = issue
        self.refresh_comments()

    def refresh_comments(self):
        self._comments = self._issue.get_comments()

    def compose(self) -> ComposeResult:
        self._vertical = Vertical(
            GithubComment(self._issue),
            *[GithubComment(comment) for comment in self._comments]
        )
        yield self._vertical


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
        self.comment = self._issue_comment.body

    def watch_comment(self, comment: str):
        self._body.update(Markdown(comment))

    async def on_click(self) -> None:
        if self.editable:
            await self.emit(self.Selected(self))

    async def key_enter(self, event: events.Key) -> None:
        if self.editable:
            await self.emit(self.Selected(self))




class GithubNotifications(SelectableDataTable):
    notifications = reactive([], layout=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_columns("repository", "subject", "reason")

    def watch_notifications(self, notifications: List[Notification]):
        self.clear()
        for notification in self.notifications:
            self.add_row(
                notification.repository.full_name,
                notification.subject.title,
                notification.reason,
            )

    def get_current_selected(self):
        return self.notifications[self.cursor_cell.row]
