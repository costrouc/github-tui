import tempfile
import subprocess
import webbrowser

from github.Repository import Repository
from github.Issue import Issue

from textual.screen import Screen
from textual.widgets import Footer, Header, Input
from textual.app import ComposeResult

from github_tui.widgets import (
    GithubRepositories,
    GithubProfile,
    GithubIssue,
    GithubRepository,
    GithubNotifications,
    SelectableDataTable,
    EmacsInput,
)
from github_tui.github import github_client


class GithubRepositoriesScreen(Screen):
    BINDINGS = [
        ("slash,ctrl+s", "search", "Search"),
    ]

    MAX_REPOSITORIES = 100

    def compose(self) -> ComposeResult:
        self._github_repositories = GithubRepositories()
        self._input = EmacsInput()
        self._input.placeholder = "Search Repositories"

        yield Header()
        yield self._input
        yield self._github_repositories
        yield Footer()

    def on_selectable_data_table_selected(
        self, message: SelectableDataTable.Selected
    ) -> None:
        self.app.push_screen(GithubRepositoryScreen(message.value))

    def on_input_submitted(self, message: Input.Submitted) -> None:
        repositories = list(
            github_client.search_repositories(message.value)[: self.MAX_REPOSITORIES]
        )
        self._github_repositories.repositories = repositories
        self._github_repositories.focus()

    def action_search(self):
        self._input.focus()

    def on_mount(self) -> None:
        self._input.focus()
        self.query_one("HeaderTitle").text = "Repositories"
        self.query_one("HeaderTitle").sub_text = ""


class GithubRepositoryScreen(Screen):
    BINDINGS = [
        ("g", "goto", "Goto"),
        ("c", "create_issue", "Create Issue"),
    ]

    def __init__(self, repository: Repository, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._repository = repository

    def compose(self) -> ComposeResult:
        self._github_repository = GithubRepository(self._repository)

        yield Header()
        yield self._github_repository
        yield Footer()

    def on_selectable_data_table_selected(
        self, message: SelectableDataTable.Selected
    ) -> None:
        self.app.push_screen(GithubIssueScreen(message.value))

    def action_goto(self) -> None:
        webbrowser.open_new_tab(self._repository.html_url)

    def action_create_issue(self) -> None:
        self.app._driver.stop_application_mode()
        with tempfile.NamedTemporaryFile(suffix=".md") as tempf:
            subprocess.run(f"$EDITOR {tempf.name}", shell=True)

            with open(tempf.name) as f:
                issue_title = f.readline()
                issue_body = f.read()

        self.app._driver.start_application_mode()

        if issue_title and issue_body:
            issue = self._repository.create_issue(
                issue_title,
                issue_body,
            )
            self.app.push_screen(GithubIssueScreen(issue))

    def on_mount(self) -> None:
        self._github_repository._github_issues.focus()
        self.query_one("HeaderTitle").text = self._repository.full_name
        self.query_one("HeaderTitle").sub_text = ""


class GithubProfileScreen(Screen):
    BINDINGS = [
        ("g", "goto", "Goto"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._profile = github_client.get_user()

    def compose(self) -> ComposeResult:
        yield Header()
        yield GithubProfile(self._profile)
        yield Footer()

    def action_goto(self) -> None:
        webbrowser.open_new_tab(self._profile.html_url)

    def on_mount(self) -> None:
        self.query_one("HeaderTitle").text = self._profile.name
        self.query_one("HeaderTitle").sub_text = ""


class GithubIssueScreen(Screen):
    BINDINGS = [
        ("g", "goto", "Goto"),
        ("e", "edit_comment", "Edit"),
        ("c", "new_comment", "Comment"),
    ]

    CURRENT_SELECTED = None

    def __init__(self, issue: Issue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._issue = issue

    def compose(self) -> ComposeResult:
        self._github_issue = GithubIssue(self._issue)

        yield Header()
        yield self._github_issue
        yield Footer()

    def action_goto(self) -> None:
        webbrowser.open_new_tab(
            self._github_issue.get_selected_comment()._issue_comment.html_url
        )

    async def action_edit_comment(self) -> None:
        self._github_issue.get_selected_comment().action_edit()

    async def action_new_comment(self) -> None:
        await self._github_issue.action_new_comment()

    def on_mount(self) -> None:
        self._github_issue.focus()
        self.query_one("HeaderTitle").text = self._issue.title
        self.query_one(
            "HeaderTitle"
        ).sub_text = f"{self._issue.repository.full_name}#{self._issue.number}"


class GithubNotificationsScreen(Screen):
    def compose(self) -> ComposeResult:
        self._github_notifications = GithubNotifications()
        self._github_notifications.notifications = (
            github_client.get_user().get_notifications()
        )
        yield Header()
        yield self._github_notifications
        yield Footer()

    def on_selectable_data_table_selected(
        self, message: SelectableDataTable.Selected
    ) -> None:
        notification = message.value
        issue = notification.get_issue()
        self.app.push_screen(GithubIssueScreen(issue))

    def on_mount(self) -> None:
        self._github_notifications.focus()
        self.query_one("HeaderTitle").text = "Notifications"
        self.query_one("HeaderTitle").sub_text = ""
