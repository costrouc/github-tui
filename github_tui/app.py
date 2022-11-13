from textual.app import App

from github_tui.screens import (
    GithubRepositoriesScreen,
    GithubProfileScreen,
    GithubNotificationsScreen,
)


class GithubTUI(App):
    """Github TUI for issues, notifications, discussions, and PR management"""

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
        self.push_screen("repositories")
