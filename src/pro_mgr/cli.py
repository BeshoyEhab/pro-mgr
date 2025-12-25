"""
CLI module for {{name}}.
Main Click command interface with all subcommands.
"""

import sys
import json
import click
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from . import db, config, scaffold, runner, watcher, tui


console = Console()


# ============== Main CLI Group ==============

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    Pro-Mgr: A command-line tool to manage multiple projects from anywhere.
    
    Run without arguments to open the interactive dashboard.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand - run the TUI
        result = tui.run_tui()
        
        if result:
            action = result[0]
            if action == "run":
                _, project_name, task_name, watch_mode = result
                _execute_task(project_name, task_name, watch_mode, force=False)
            elif action == "shell":
                _, project_name = result
                _print_shell_command(project_name)


# ============== new Command ==============

@cli.command()
@click.argument("name")
@click.option("--template", "-t", default="python-cli", 
              help="Project template (python-cli, flask-api, django-app)")
@click.option("--path", "-p", default=".", help="Directory to create project in")
@click.option("--no-git", is_flag=True, help="Skip Git initialization")
@click.option("--no-venv", is_flag=True, help="Skip virtual environment creation")
def new(name: str, template: str, path: str, no_git: bool, no_venv: bool):
    """
    Create a new project from a template.
    
    Examples:
    
        pro-mgr new my-app
        
        pro-mgr new my-api --template flask-api
        
        pro-mgr new my-blog --path ~/projects/
    """
    try:
        console.print(f"[bold cyan]Creating project:[/] {name}")
        console.print(f"  Template: {template}")
        console.print(f"  Path: {Path(path).resolve() / name}")
        console.print()
        
        result = scaffold.create_project(
            name=name,
            template=template,
            path=path,
            init_git_repo=not no_git,
            create_venv_env=not no_venv,
        )
        
        console.print("[bold green]✓[/] Project created successfully!")
        console.print()
        console.print(f"  📁 Path: {result['path']}")
        
        if result['git_initialized']:
            console.print("  🔀 Git: initialized")
        
        if result['venv_path']:
            console.print(f"  🐍 Venv: {result['venv_path']}")
        
        console.print()
        console.print("[dim]Next steps:[/]")
        console.print(f"  cd {result['path']}")
        console.print(f"  pro-mgr run {name} test")
        
    except FileExistsError as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)
    except scaffold.TemplateNotFoundError as e:
        console.print(f"[bold red]Error:[/] {e}")
        available = scaffold.get_available_templates()
        if available:
            console.print(f"[dim]Available templates: {', '.join(available)}[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)


# ============== run Command ==============

@cli.command()
@click.argument("project_name")
@click.argument("task_name")
@click.option("--watch", "-w", is_flag=True, help="Auto-rerun on file changes")
@click.option("--force", "-f", is_flag=True, help="Skip Git dirty state check")
def run(project_name: str, task_name: str, watch: bool, force: bool):
    """
    Run a task for a project.
    
    Works from any directory.
    
    Examples:
    
        pro-mgr run my-api test
        
        pro-mgr run my-app serve --watch
        
        pro-mgr run my-api deploy --force
    """
    _execute_task(project_name, task_name, watch, force)


def _execute_task(project_name: str, task_name: str, watch: bool, force: bool):
    """Execute a task with optional watch mode."""
    try:
        if watch:
            # Get project info for watch directories
            project = db.get_project(project_name)
            if not project:
                console.print(f"[bold red]Error:[/] Project not found: {project_name}")
                sys.exit(1)
            
            # Load config to get watch_dirs
            try:
                proj_config = config.load_config(project['root_path'])
                task = config.get_task(proj_config, task_name)
                watch_dirs = task.get('watch_dirs', []) if task else []
            except Exception:
                watch_dirs = []
            
            # Resolve watch directories
            dirs = watcher.resolve_watch_dirs(project['root_path'], watch_dirs)
            
            # Run with watcher
            def run_callback():
                try:
                    runner.run_task(project_name, task_name, force)
                except Exception as e:
                    console.print(f"[bold red]Error:[/] {e}")
            
            watcher.watch_and_execute(
                dirs=dirs,
                callback=run_callback,
                project_path=project['root_path']
            )
        else:
            # Single run
            exit_code = runner.run_task(project_name, task_name, force)
            sys.exit(exit_code)
            
    except runner.GitDirtyError as e:
        console.print(f"[bold red]Error:[/] {e}")
        console.print("[dim]Use --force to run anyway[/]")
        sys.exit(1)
    except runner.RunnerError as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted[/]")
        sys.exit(130)


# ============== shell Command ==============

@cli.command()
@click.argument("project_name")
def shell(project_name: str):
    """
    Print shell command to activate project environment.
    
    Usage:
    
        eval $(pro-mgr shell my-project)
    
    This will:
    - Change to the project directory
    - Activate the virtual environment (if exists)
    """
    _print_shell_command(project_name)


def _print_shell_command(project_name: str):
    """Print the shell activation command."""
    try:
        cmd = runner.get_shell_activation_command(project_name)
        print(cmd)
    except runner.RunnerError as e:
        console.print(f"[bold red]Error:[/] {e}", err=True)
        sys.exit(1)


# ============== project Command Group ==============

@cli.group()
def project():
    """Manage registered projects."""
    pass


@project.command("list")
@click.option("--format", "-f", "fmt", type=click.Choice(["table", "json"]), 
              default="table", help="Output format")
def project_list(fmt: str):
    """List all registered projects."""
    projects = db.get_all_projects()
    
    if fmt == "json":
        print(json.dumps(projects, indent=2, default=str))
    else:
        if not projects:
            console.print("[dim]No projects registered. Use 'pro-mgr new' or 'pro-mgr project add'.[/]")
            return
        
        table = Table(title="Registered Projects")
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="dim")
        table.add_column("Tags", style="yellow")
        
        for p in projects:
            table.add_row(
                p['name'],
                p['root_path'],
                p.get('tags') or ""
            )
        
        console.print(table)


@project.command("info")
@click.argument("project_name")
def project_info(project_name: str):
    """Show detailed project information."""
    project = db.get_project(project_name)
    
    if not project:
        console.print(f"[bold red]Error:[/] Project not found: {project_name}")
        sys.exit(1)
    
    console.print(Panel(f"[bold cyan]{project['name']}[/]", expand=False))
    console.print(f"[bold]Path:[/] {project['root_path']}")
    
    if project.get('description'):
        console.print(f"[bold]Description:[/] {project['description']}")
    
    if project.get('tags'):
        console.print(f"[bold]Tags:[/] {project['tags']}")
    
    if project.get('venv_path'):
        console.print(f"[bold]Venv:[/] {project['venv_path']}")
    
    console.print(f"[bold]Created:[/] {project.get('created_at', 'N/A')}")
    console.print(f"[bold]Last accessed:[/] {project.get('last_accessed', 'N/A')}")
    
    # Show tasks if config exists
    try:
        proj_config = config.load_config(project['root_path'])
        tasks = config.get_all_tasks(proj_config)
        
        if tasks:
            console.print()
            console.print("[bold]Available Tasks:[/]")
            for name, task in tasks.items():
                desc = task.get('description', '')
                console.print(f"  [green]▶ {name}[/] - {desc}")
    except FileNotFoundError:
        console.print("\n[dim]No pro-mgr.toml found[/]")


@project.command("add")
@click.argument("path", type=click.Path(exists=True))
@click.option("--name", "-n", help="Custom project name (default: directory name)")
def project_add(path: str, name: Optional[str]):
    """Register an existing project directory."""
    path = Path(path).resolve()
    
    if name is None:
        name = path.name
    
    # Check if already exists
    if db.project_exists(name):
        console.print(f"[bold red]Error:[/] Project '{name}' already registered")
        sys.exit(1)
    
    # Detect venv
    venv_path = scaffold.detect_venv(str(path))
    
    # Check for pro-mgr.toml
    config_path = path / "pro-mgr.toml"
    if not config_path.exists():
        console.print("[yellow]Warning:[/] No pro-mgr.toml found. Create one to define tasks.")
    
    # Add to database
    if db.add_project(
        name=name,
        root_path=str(path),
        venv_path=str(venv_path) if venv_path else None
    ):
        console.print(f"[bold green]✓[/] Registered project: {name}")
        console.print(f"  Path: {path}")
        if venv_path:
            console.print(f"  Venv: {venv_path}")
    else:
        console.print(f"[bold red]Error:[/] Failed to register project")
        sys.exit(1)


@project.command("rm")
@click.argument("project_name")
@click.option("--confirm", "-y", is_flag=True, help="Skip confirmation")
def project_rm(project_name: str, confirm: bool):
    """Remove a project from the registry (files are preserved)."""
    project = db.get_project(project_name)
    
    if not project:
        console.print(f"[bold red]Error:[/] Project not found: {project_name}")
        sys.exit(1)
    
    if not confirm:
        console.print(f"Remove [cyan]{project_name}[/] from registry?")
        console.print(f"[dim]Path: {project['root_path']}[/]")
        console.print("[dim](Files will NOT be deleted)[/]")
        if not click.confirm("Continue?"):
            console.print("[dim]Cancelled[/]")
            return
    
    if db.delete_project(project_name):
        console.print(f"[bold green]✓[/] Removed {project_name} from registry")
    else:
        console.print(f"[bold red]Error:[/] Failed to remove project")
        sys.exit(1)


@project.command("update")
@click.argument("project_name")
@click.option("--description", "-d", help="Project description")
@click.option("--tags", "-t", help="Comma-separated tags")
def project_update(project_name: str, description: Optional[str], tags: Optional[str]):
    """Update project metadata."""
    project = db.get_project(project_name)
    
    if not project:
        console.print(f"[bold red]Error:[/] Project not found: {project_name}")
        sys.exit(1)
    
    updates = {}
    if description is not None:
        updates['description'] = description
    if tags is not None:
        updates['tags'] = tags
    
    if not updates:
        console.print("[dim]Nothing to update. Use --description or --tags.[/]")
        return
    
    if db.update_project(project_name, **updates):
        console.print(f"[bold green]✓[/] Updated {project_name}")
    else:
        console.print(f"[bold red]Error:[/] Failed to update project")
        sys.exit(1)


# ============== snip Command Group ==============

@cli.group()
def snip():
    """Manage code snippets."""
    pass


@snip.command("add")
@click.option("--name", "-n", required=True, help="Snippet name")
@click.option("--tags", "-t", help="Comma-separated tags")
def snip_add(name: str, tags: Optional[str]):
    """Create a new snippet (opens editor)."""
    if db.get_snippet(name):
        console.print(f"[bold red]Error:[/] Snippet '{name}' already exists")
        sys.exit(1)
    
    # Open editor for content
    content = click.edit("# Enter your command/snippet here\n")
    
    if content is None:
        console.print("[dim]Cancelled[/]")
        return
    
    content = content.strip()
    if not content or content == "# Enter your command/snippet here":
        console.print("[dim]Empty content, cancelled[/]")
        return
    
    if db.add_snippet(name, content, tags):
        console.print(f"[bold green]✓[/] Created snippet: {name}")
    else:
        console.print(f"[bold red]Error:[/] Failed to create snippet")
        sys.exit(1)


@snip.command("ls")
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--format", "-f", "fmt", type=click.Choice(["table", "json"]), 
              default="table", help="Output format")
def snip_ls(tag: Optional[str], fmt: str):
    """List all snippets."""
    snippets = db.get_all_snippets(tag)
    
    if fmt == "json":
        print(json.dumps(snippets, indent=2, default=str))
    else:
        if not snippets:
            msg = f"No snippets found"
            if tag:
                msg += f" with tag '{tag}'"
            console.print(f"[dim]{msg}[/]")
            return
        
        table = Table(title="Code Snippets")
        table.add_column("Name", style="cyan")
        table.add_column("Tags", style="yellow")
        table.add_column("Uses", justify="right")
        table.add_column("Preview", style="dim", max_width=40)
        
        for s in snippets:
            preview = s['content'][:40].replace('\n', ' ')
            if len(s['content']) > 40:
                preview += "..."
            
            table.add_row(
                s['name'],
                s.get('tags') or "",
                str(s.get('usage_count', 0)),
                preview
            )
        
        console.print(table)


@snip.command("search")
@click.argument("query")
def snip_search(query: str):
    """Search snippets by name, content, or tags."""
    snippets = db.search_snippets(query)
    
    if not snippets:
        console.print(f"[dim]No snippets matching '{query}'[/]")
        return
    
    console.print(f"[bold]Found {len(snippets)} snippets matching '{query}':[/]\n")
    
    for s in snippets:
        console.print(f"[cyan bold]{s['name']}[/] [yellow]({s.get('tags') or 'no tags'})[/]")
        console.print(Syntax(s['content'], "bash", theme="monokai", line_numbers=False))
        console.print()


@snip.command("show")
@click.argument("name")
def snip_show(name: str):
    """Display a snippet's content."""
    snippet = db.get_snippet(name)
    
    if not snippet:
        console.print(f"[bold red]Error:[/] Snippet not found: {name}")
        sys.exit(1)
    
    console.print(Panel(
        Syntax(snippet['content'], "bash", theme="monokai"),
        title=f"[cyan]{name}[/]",
        subtitle=f"[yellow]{snippet.get('tags') or 'no tags'}[/]"
    ))


@snip.command("edit")
@click.argument("name")
def snip_edit(name: str):
    """Edit an existing snippet."""
    snippet = db.get_snippet(name)
    
    if not snippet:
        console.print(f"[bold red]Error:[/] Snippet not found: {name}")
        sys.exit(1)
    
    # Open editor with existing content
    new_content = click.edit(snippet['content'])
    
    if new_content is None:
        console.print("[dim]Cancelled[/]")
        return
    
    new_content = new_content.strip()
    if not new_content:
        console.print("[dim]Empty content, cancelled[/]")
        return
    
    if db.update_snippet(name, content=new_content):
        console.print(f"[bold green]✓[/] Updated snippet: {name}")
    else:
        console.print(f"[bold red]Error:[/] Failed to update snippet")
        sys.exit(1)


@snip.command("rm")
@click.argument("name")
@click.option("--confirm", "-y", is_flag=True, help="Skip confirmation")
def snip_rm(name: str, confirm: bool):
    """Delete a snippet."""
    snippet = db.get_snippet(name)
    
    if not snippet:
        console.print(f"[bold red]Error:[/] Snippet not found: {name}")
        sys.exit(1)
    
    if not confirm:
        console.print(f"Delete snippet [cyan]{name}[/]?")
        if not click.confirm("Continue?"):
            console.print("[dim]Cancelled[/]")
            return
    
    if db.delete_snippet(name):
        console.print(f"[bold green]✓[/] Deleted snippet: {name}")
    else:
        console.print(f"[bold red]Error:[/] Failed to delete snippet")
        sys.exit(1)


# ============== Entry Point ==============

def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
