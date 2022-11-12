import tempfile
import subprocess
import os

from github import Github
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual import events
from textual.containers import Container
from textual.widgets import Footer, Header, Static, DataTable

from textual_github.screens import (
    GithubIssueScreen,
    GithubRepositoriesScreen,
    GithubProfileScreen,
    GithubNotificationsScreen
)


class GithubApp(App):
    """A working 'desktop' github application."""

    CSS_PATH = "styles.css"

    SCREENS = {
        "repositories": GithubRepositoriesScreen(),
        "profile": GithubProfileScreen(),
        "notifications": GithubNotificationsScreen(),
    }

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "push_screen('repositories')", "Repositories"),
        ("p", "push_screen('profile')", "Profile"),
        ("n", "push_screen('notifications')", "Notifications"),
    ]

    def on_mount(self) -> None:
        self.push_screen('profile')
