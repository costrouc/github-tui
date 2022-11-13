from typing import List
import tempfile
import subprocess

from github.Repository import Repository
from github.NamedUser import NamedUser
from github.Issue import Issue
from github.IssueComment import IssueComment
from github.Notification import Notification

from textual.reactive import reactive
from rich.markdown import Markdown
from rich.panel import Panel

from textual import events
from textual.app import ComposeResult
from textual.message import Message, MessageTarget
from textual.widgets import Static
from textual.widget import Widget
from textual.containers import Vertical

from github_tui.widgets.ui import SelectableDataTable


class GithubProfile(Widget):
    def __init__(self, user: NamedUser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user

    def compose(self) -> ComposeResult:
        yield Static(
            Markdown(
                f"""
# {self._user.name}

 - company {self._user.company}
 - email {self._user.email}

```{self._user.bio}```
"""
            )
        )


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
                str(repository.stargazers_count),
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
            Static(
                Markdown(
                    f"""
{self._repository.description}

 - stars :: {self._repository.stargazers_count}
 - forks :: {self._repository.forks_count}
 - open issues :: {self._repository.open_issues_count}
 - private :: {self._repository.private}
 - size :: {self._repository.size}
 - topics :: {self._repository.topics}

## Issues
"""
                )
            ),
            self._github_issues,
        )


class GithubComment(Static):
    class Selected(Message):
        """Element selected message."""

        def __init__(self, sender: MessageTarget) -> None:
            self.sender = sender
            super().__init__(sender)

    comment = reactive('Edit (click and press "e")', layout=True)
    editable = reactive(True)
    active = reactive(False)

    def __init__(
        self, issue_comment: IssueComment, editable: bool = True, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._issue_comment = issue_comment
        self.comment = self._issue_comment.body
        self.editable = editable

    def render(self) -> Panel:
        return Panel(
            Markdown(self.comment),
            title=f"@{self._issue_comment.user.login}",
            title_align="left",
            subtitle=str(self._issue_comment.created_at),
            border_style="white" if self.active else "grey23",
        )

    def action_edit(self) -> None:
        self.app._driver.stop_application_mode()
        with tempfile.NamedTemporaryFile(suffix=".md") as tempf:
            with open(tempf.name, "w") as f:
                f.write(self.comment)

            subprocess.run(f"$EDITOR {tempf.name}", shell=True)

            with open(tempf.name) as f:
                comment_body = f.read()
                self._issue_comment.edit(comment_body)
                self.comment = comment_body
        self.app._driver.start_application_mode()

    async def on_click(self) -> None:
        if self.editable:
            await self.emit(self.Selected(self))

    async def key_enter(self, event: events.Key) -> None:
        if self.editable:
            await self.emit(self.Selected(self))


class GithubIssues(SelectableDataTable):
    issues = reactive([], layout=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_columns("number", "title", "comments")

    def watch_issues(self, issues: List[Issue]):
        for issue in self.issues:
            self.add_row(str(issue.number), issue.title, str(issue.comments))

    def get_current_selected(self):
        return self.issues[self.cursor_cell.row]


class GithubIssue(Widget, can_focus=True):
    def __init__(self, issue: Issue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._issue = issue
        self._comments = list(self._issue.get_comments())
        self._github_comments = []
        self._index = 0

    def compose(self) -> ComposeResult:
        self._github_comments.append(GithubComment(self._issue, classes="active"))
        self._github_comments.extend(
            [GithubComment(comment) for comment in self._comments]
        )
        self._vertical = Vertical(*self._github_comments)
        yield self._vertical

    def on_mount(self):
        self.get_selected_comment().active = True

    def get_selected_comment(self):
        return self.query("GithubComment")[self._index]

    def action_selection_down(self):
        self.get_selected_comment().active = False
        self._index = min(max(0, self._index + 1), len(self._comments))
        self.get_selected_comment().active = True

    def action_selection_up(self):
        self.get_selected_comment().active = False
        self._index = min(max(0, self._index - 1), len(self._comments))
        self.get_selected_comment().active = True

    async def action_new_comment(self):
        self.app._driver.stop_application_mode()
        with tempfile.NamedTemporaryFile(suffix=".md") as tempf:
            subprocess.run(f"$EDITOR {tempf.name}", shell=True)

            with open(tempf.name) as f:
                comment_body = f.read()

        self.app._driver.start_application_mode()

        if comment_body:
            issue_comment = self._issue.create_comment(comment_body)
            self._comments.append(issue_comment)
            github_comment = GithubComment(issue_comment)
            self._github_comments.append(github_comment)
            await self._vertical.mount(github_comment, after=-1)

    def on_github_comment_selected(self, message: GithubComment.Selected) -> None:
        github_comment = message.sender
        self.get_selected_comment().active = False
        self._index = self._github_comments.index(github_comment)
        self.get_selected_comment().active = True

    def on_key(self, event: events.Key) -> None:
        self.log(event.key)
        if event.key == "ctrl+n" or event.key == "down":
            self.action_selection_down()
            event.stop()
            event.prevent_default()
        elif event.key == "ctrl+p" or event.key == "up":
            self.action_selection_up()
            event.stop()
            event.prevent_default()


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
