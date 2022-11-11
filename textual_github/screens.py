import tempfile
import subprocess
import webbrowser

from github.Repository import Repository
from github.Issue import Issue

from textual.screen import Screen
from textual.widgets import Footer, Header
from textual.app import ComposeResult

from textual_github.widgets import GithubRepositories, GithubProfile, GithubIssue, GithubIssues, GithubComment, GithubRepository
from textual_github.github import github_client


class GithubRepositoriesScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield GithubRepositories(github_client.search_repositories('user:costrouc'))
        yield Footer()

    def on_github_repositories_selected(self, message: GithubRepositories.Selected) -> None:
        self.app.push_screen(GithubRepositoryScreen(message.repository))


class GithubRepositoryScreen(Screen):
    BINDINGS = [
        ("g", "goto", "Goto"),
    ]

    def __init__(self, repository: Repository, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._repository = repository

    def compose(self) -> ComposeResult:
        yield Header()
        yield GithubRepository(self._repository)
        yield Footer()

    def on_github_issues_selected(self, message: GithubIssues.Selected) -> None:
        self.app.push_screen(GithubIssueScreen(message.issue))

    def action_goto(self) -> None:
        webbrowser.open_new_tab(self._repository.html_url)


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


class GithubIssueScreen(Screen):
    BINDINGS = [
        ("g", "goto", "Goto"),
        ("e", "edit", "Edit"),
    ]

    CURRENT_SELECTED = None

    def __init__(self, issue: Issue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._issue = issue

    def compose(self) -> ComposeResult:
        yield Header()
        yield GithubIssue(self._issue)
        yield Footer()

    def action_goto(self) -> None:
        webbrowser.open_new_tab(self._issue.html_url)

    def on_github_comment_selected(self, message: GithubComment.Selected) -> None:
        if self.CURRENT_SELECTED is not None:
            self.CURRENT_SELECTED.active = False
        self.CURRENT_SELECTED = message.sender
        self.CURRENT_SELECTED.active = True

    async def action_edit(self) -> None:
        if self.CURRENT_SELECTED:
            self.app._driver.stop_application_mode()
            with tempfile.NamedTemporaryFile(suffix=".md") as tempf:
                with open(tempf.name, "w") as f:
                    f.write(self.CURRENT_SELECTED.comment)

                subprocess.run(f"$EDITOR {tempf.name}", shell=True)

                with open(tempf.name) as f:
                    self.CURRENT_SELECTED.comment = f.read()
            self.app._driver.start_application_mode()
