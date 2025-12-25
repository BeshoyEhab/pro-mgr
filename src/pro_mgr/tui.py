"""
TUI module for pro-mgr.
Interactive terminal dashboard using Textual.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label
from textual.binding import Binding
from textual.screen import Screen
from rich.text import Text

from pathlib import Path
from typing import Optional, List, Dict, Any

from . import db, config


class ProjectListItem(ListItem):
    """A list item representing a project."""
    
    def __init__(self, project: Dict[str, Any]) -> None:
        super().__init__()
        self.project = project
    
    def compose(self) -> ComposeResult:
        name = self.project['name']
        path = self.project['root_path']
        tags = self.project.get('tags', '') or ''
        
        # Truncate path if too long
        max_path_len = 45
        if len(path) > max_path_len:
            path = "..." + path[-(max_path_len-3):]
        
        content = Text()
        content.append(f"📁 {name}", style="bold cyan")
        content.append(f"\n   {path}", style="dim")
        if tags:
            content.append(f"\n   🏷️  {tags}", style="yellow")
        
        yield Static(content)


class TaskListItem(ListItem):
    """A list item representing a task."""
    
    def __init__(self, task_name: str, task_config: Dict[str, Any]) -> None:
        super().__init__()
        self.task_name = task_name
        self.task_config = task_config
    
    def compose(self) -> ComposeResult:
        name = self.task_name
        desc = self.task_config.get('description', '')
        cmd = self.task_config.get('command', '')
        
        # Truncate command if too long
        if len(cmd) > 50:
            cmd = cmd[:47] + "..."
        
        content = Text()
        content.append(f"▶ {name}", style="bold green")
        if desc:
            content.append(f" - {desc}", style="dim")
        content.append(f"\n   $ {cmd}", style="italic dim")
        
        yield Static(content)


class HelpScreen(Screen):
    """Help screen showing keyboard shortcuts."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(self._render_help(), id="help-content"),
            id="help-container",
        )
    
    def _render_help(self) -> Text:
        text = Text()
        text.append("Pro-Mgr Dashboard Help\n\n", style="bold cyan")
        
        text.append("Project List:\n", style="bold")
        shortcuts = [
            ("↑/↓", "Navigate projects"),
            ("Enter", "Enter project (view tasks)"),
            ("s", "Open shell in project"),
            ("d", "Delete project from registry"),
        ]
        for key, desc in shortcuts:
            text.append(f"  {key:<10}", style="bold green")
            text.append(f"{desc}\n")
        
        text.append("\nTask List:\n", style="bold")
        shortcuts = [
            ("↑/↓", "Navigate tasks"),
            ("Enter/r", "Run selected task"),
            ("w", "Run task in watch mode"),
            ("Backspace", "Go back to projects"),
        ]
        for key, desc in shortcuts:
            text.append(f"  {key:<10}", style="bold green")
            text.append(f"{desc}\n")
        
        text.append("\nGeneral:\n", style="bold")
        shortcuts = [
            ("?", "Show this help"),
            ("q", "Quit"),
        ]
        for key, desc in shortcuts:
            text.append(f"  {key:<10}", style="bold green")
            text.append(f"{desc}\n")
        
        text.append("\n\nPress ESC or Q to close", style="dim")
        return text
    
    def action_dismiss(self) -> None:
        self.app.pop_screen()


class ProMgrApp(App):
    """Main TUI application for pro-mgr."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        layout: horizontal;
        height: 100%;
    }
    
    #left-panel {
        width: 50%;
        border: solid $primary;
        padding: 1;
    }
    
    #right-panel {
        width: 50%;
        border: solid $secondary;
        padding: 1;
    }
    
    #project-list, #task-list {
        height: 100%;
    }
    
    .panel-header {
        text-style: bold;
        padding: 0 0 1 0;
    }
    
    ProjectListItem {
        padding: 1;
    }
    
    ProjectListItem:hover {
        background: $surface-lighten-1;
    }
    
    ProjectListItem.-selected {
        background: $primary-darken-2;
    }
    
    TaskListItem {
        padding: 1;
    }
    
    TaskListItem:hover {
        background: $surface-lighten-1;
    }
    
    #help-container {
        align: center middle;
        width: 60;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 2;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    
    .hidden {
        display: none;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "run_task", "Run"),
        Binding("w", "watch_task", "Watch"),
        Binding("s", "open_shell", "Shell"),
        Binding("d", "delete_project", "Delete"),
        Binding("backspace", "go_back", "Back"),
        Binding("escape", "go_back_or_quit", "Back/Quit", show=False),
        Binding("?", "show_help", "Help"),
    ]
    
    TITLE = "Pro-Mgr Dashboard"
    
    def __init__(self) -> None:
        super().__init__()
        self.projects: List[Dict[str, Any]] = []
        self.selected_project: Optional[Dict[str, Any]] = None
        self.selected_task: Optional[str] = None
        self.in_project_view: bool = False  # True when viewing tasks
        self.tasks: Dict[str, Any] = {}
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Vertical(
                Static("📁 Projects (Enter to select)", classes="panel-header", id="left-header"),
                ListView(id="project-list"),
                id="left-panel",
            ),
            Vertical(
                Static("Select a project to view tasks", classes="panel-header", id="right-header"),
                ListView(id="task-list"),
                id="right-panel",
            ),
            id="main-container",
        )
        yield Static("↑↓ Navigate | Enter: Select | ?: Help | q: Quit", id="status-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self._refresh_projects()
        # Focus the project list
        self.query_one("#project-list", ListView).focus()
    
    def _refresh_projects(self) -> None:
        """Refresh the project list from database."""
        self.projects = db.get_all_projects()
        
        project_list = self.query_one("#project-list", ListView)
        project_list.clear()
        
        if not self.projects:
            project_list.append(ListItem(Static("No projects found.\nUse 'pro-mgr new' to create one.")))
        else:
            for project in self.projects:
                project_list.append(ProjectListItem(project))
    
    def _load_tasks(self) -> None:
        """Load tasks for the selected project."""
        if not self.selected_project:
            return
        
        task_list = self.query_one("#task-list", ListView)
        task_list.clear()
        
        try:
            proj_config = config.load_config(self.selected_project['root_path'])
            self.tasks = config.get_all_tasks(proj_config)
            
            if self.tasks:
                for name, cfg in self.tasks.items():
                    task_list.append(TaskListItem(name, cfg))
            else:
                task_list.append(ListItem(Static("No tasks defined in pro-mgr.toml")))
        except FileNotFoundError:
            task_list.append(ListItem(Static("No pro-mgr.toml found")))
            self.tasks = {}
        except Exception as e:
            task_list.append(ListItem(Static(f"Error loading tasks: {e}")))
            self.tasks = {}
    
    def _enter_project(self, project: Dict[str, Any]) -> None:
        """Enter a project and show its tasks."""
        self.selected_project = project
        self.in_project_view = True
        self.selected_task = None
        
        # Update headers
        left_header = self.query_one("#left-header", Static)
        left_header.update(f"📁 {project['name']}")
        
        right_header = self.query_one("#right-header", Static)
        right_header.update("📋 Tasks (Enter to run, Backspace to go back)")
        
        # Load tasks
        self._load_tasks()
        
        # Focus the task list
        task_list = self.query_one("#task-list", ListView)
        task_list.focus()
        
        self._update_status(f"Project: {project['name']} | r: Run | w: Watch | Backspace: Back")
    
    def _go_back_to_projects(self) -> None:
        """Go back to the project list."""
        self.in_project_view = False
        self.selected_task = None
        
        # Update headers
        left_header = self.query_one("#left-header", Static)
        left_header.update("📁 Projects (Enter to select)")
        
        right_header = self.query_one("#right-header", Static)
        right_header.update("Select a project to view tasks")
        
        # Clear task list
        task_list = self.query_one("#task-list", ListView)
        task_list.clear()
        
        # Focus the project list
        project_list = self.query_one("#project-list", ListView)
        project_list.focus()
        
        self._update_status("↑↓ Navigate | Enter: Select | ?: Help | q: Quit")
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection (Enter key pressed)."""
        item = event.item
        
        if isinstance(item, ProjectListItem):
            # Enter the project
            self._enter_project(item.project)
        elif isinstance(item, TaskListItem):
            # Run the task
            self.selected_task = item.task_name
            self._run_selected_task(watch=False)
    
    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle highlight changes (arrow key navigation)."""
        item = event.item
        
        if isinstance(item, ProjectListItem):
            self.selected_project = item.project
            # Show preview in right panel
            if not self.in_project_view:
                self._preview_project(item.project)
        elif isinstance(item, TaskListItem):
            self.selected_task = item.task_name
    
    def _preview_project(self, project: Dict[str, Any]) -> None:
        """Show a preview of the project with its tasks in the right panel."""
        right_header = self.query_one("#right-header", Static)
        right_header.update(f"� Tasks for {project['name']} (Enter to select)")
        
        task_list = self.query_one("#task-list", ListView)
        task_list.clear()
        
        # Show project info first
        info = Text()
        info.append(f"📁 {project['name']}\n", style="bold cyan")
        info.append(f"Path: {project['root_path']}\n", style="dim")
        if project.get('venv_path'):
            info.append(f"Venv: ✓\n", style="green")
        
        task_list.append(ListItem(Static(info)))
        
        # Load and show tasks
        try:
            proj_config = config.load_config(project['root_path'])
            tasks = config.get_all_tasks(proj_config)
            
            if tasks:
                task_list.append(ListItem(Static("\n📋 Available Tasks:", id="tasks-header")))
                for name, cfg in tasks.items():
                    task_list.append(TaskListItem(name, cfg))
            else:
                task_list.append(ListItem(Static("\nNo tasks defined in pro-mgr.toml")))
        except FileNotFoundError:
            task_list.append(ListItem(Static("\n⚠️ No pro-mgr.toml found")))
        except Exception as e:
            task_list.append(ListItem(Static(f"\n⚠️ Error: {e}")))
    
    def _run_selected_task(self, watch: bool = False) -> None:
        """Run the currently selected task."""
        if not self.selected_project or not self.selected_task:
            return
        
        mode = "watch mode" if watch else ""
        self._update_status(f"Running {self.selected_task} {mode}...")
        self.exit(result=("run", self.selected_project['name'], self.selected_task, watch))
    
    def _update_status(self, message: str) -> None:
        """Update the status bar message."""
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(message)
    
    def action_show_help(self) -> None:
        """Show the help screen."""
        self.push_screen(HelpScreen())
    
    def action_run_task(self) -> None:
        """Run the selected task."""
        if not self.in_project_view:
            self._update_status("Enter a project first (press Enter)")
            return
        
        if not self.selected_task:
            self._update_status("Select a task first")
            return
        
        self._run_selected_task(watch=False)
    
    def action_watch_task(self) -> None:
        """Run the selected task in watch mode."""
        if not self.in_project_view:
            self._update_status("Enter a project first (press Enter)")
            return
        
        if not self.selected_task:
            self._update_status("Select a task first")
            return
        
        self._run_selected_task(watch=True)
    
    def action_open_shell(self) -> None:
        """Open shell in the selected project."""
        if not self.selected_project:
            self._update_status("Select a project first")
            return
        
        self.exit(result=("shell", self.selected_project['name']))
    
    def action_delete_project(self) -> None:
        """Delete the selected project from registry."""
        if not self.selected_project:
            self._update_status("Select a project first")
            return
        
        if self.in_project_view:
            self._update_status("Go back to project list first (Backspace)")
            return
        
        # Delete from database (files are preserved)
        name = self.selected_project['name']
        if db.delete_project(name):
            self._update_status(f"Removed {name} from registry (files preserved)")
            self.selected_project = None
            self._refresh_projects()
        else:
            self._update_status(f"Failed to remove {name}")
    
    def action_go_back(self) -> None:
        """Go back to the project list."""
        if self.in_project_view:
            self._go_back_to_projects()
    
    def action_go_back_or_quit(self) -> None:
        """Go back if in project view, otherwise quit."""
        if self.in_project_view:
            self._go_back_to_projects()
        else:
            self.exit()


def run_tui() -> Optional[tuple]:
    """
    Run the TUI application.
    
    Returns:
        Tuple with action info or None if just quit
    """
    app = ProMgrApp()
    return app.run()
