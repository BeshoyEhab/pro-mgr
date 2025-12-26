"""
Scaffold module for {{name}}.
Handles project creation, templates, and initialization.
"""

import os
import shutil
import subprocess
import platform
from pathlib import Path
from typing import List, Optional

from . import db


class ScaffoldError(Exception):
    """Base exception for scaffolding errors."""
    pass


class TemplateNotFoundError(ScaffoldError):
    """Raised when a template doesn't exist."""
    pass


def get_default_variables() -> dict:
    """
    Get default template variables from user config or environment.
    
    Reads from ~/.pro-mgr/config.toml if exists, otherwise uses defaults.
    
    Returns:
        Dict with default values for author, email, license, etc.
    """
    import os
    import getpass
    
    defaults = {
        'author': getpass.getuser(),
        'email': '',
        'license': 'MIT',
        'description': '',
        'python_version': '3.10',
    }
    
    # Try to load from config file
    config_path = Path.home() / '.pro-mgr' / 'config.toml'
    if config_path.exists():
        try:
            import toml
            user_config = toml.load(config_path)
            defaults.update(user_config.get('defaults', {}))
        except Exception:
            pass  # Ignore config errors, use defaults
    
    # Override with environment variables
    if os.environ.get('PRO_MGR_AUTHOR'):
        defaults['author'] = os.environ['PRO_MGR_AUTHOR']
    if os.environ.get('PRO_MGR_EMAIL'):
        defaults['email'] = os.environ['PRO_MGR_EMAIL']
    if os.environ.get('PRO_MGR_LICENSE'):
        defaults['license'] = os.environ['PRO_MGR_LICENSE']
    
    return defaults


def get_templates_dir() -> Path:
    """Get the path to the templates directory."""
    # Templates are in the package directory
    return Path(__file__).parent.parent.parent / "templates"


def get_available_templates() -> List[str]:
    """
    Get a list of available project templates.
    
    Returns:
        List of template names
    """
    templates_dir = get_templates_dir()
    if not templates_dir.exists():
        return []
    
    return [d.name for d in templates_dir.iterdir() if d.is_dir()]


def create_project_structure(name: str, template: str, path: str = ".", variables: dict = None) -> Path:
    """
    Create a new project from a template.
    
    Args:
        name: Project name
        template: Template name (python-cli, flask-api, django-app)
        path: Parent directory for the project
        variables: Template variables for substitution
    
    Returns:
        Path to the created project
    
    Raises:
        FileExistsError: If the project directory already exists
        TemplateNotFoundError: If the template doesn't exist
    """
    templates_dir = get_templates_dir()
    template_path = templates_dir / template
    
    if not template_path.exists():
        available = get_available_templates()
        raise TemplateNotFoundError(
            f"Template '{template}' not found. Available: {', '.join(available) or 'none'}"
        )
    
    # Create project directory
    project_path = Path(path).resolve() / name
    
    if project_path.exists():
        raise FileExistsError(f"Directory already exists: {project_path}")
    
    project_path.mkdir(parents=True)
    
    # Copy template files with variables
    _copy_template(template_path, project_path, name, variables)
    
    return project_path


def _copy_template(src: Path, dest: Path, project_name: str, variables: dict = None) -> None:
    """
    Copy template files with variable substitution.
    
    Args:
        src: Source template directory
        dest: Destination project directory
        project_name: Name to substitute for {{name}} placeholders
        variables: Additional variables for substitution
    """
    if variables is None:
        variables = {}
    
    # Build complete variable map
    var_map = get_default_variables()
    var_map.update(variables)
    var_map['name'] = project_name
    var_map['name_underscore'] = project_name.replace('-', '_')
    
    for item in src.iterdir():
        dest_name = item.name.replace("{{name}}", project_name)
        dest_path = dest / dest_name
        
        if item.is_dir():
            # Handle special __name__ directories
            if item.name == "__name__":
                dest_path = dest / project_name.replace("-", "_")
            dest_path.mkdir(parents=True, exist_ok=True)
            _copy_template(item, dest_path, project_name, variables)
        else:
            # Copy file with content substitution
            try:
                content = item.read_text()
                # Replace all variables
                for key, value in var_map.items():
                    content = content.replace(f"{{{{{key}}}}}", str(value))
                dest_path.write_text(content)
            except UnicodeDecodeError:
                # Binary file, just copy
                shutil.copy2(item, dest_path)


def init_git(project_path: str) -> bool:
    """
    Initialize a Git repository in the project.
    
    Args:
        project_path: Path to the project
    
    Returns:
        True if successful, False otherwise
    """
    try:
        subprocess.run(
            ["git", "init"],
            cwd=project_path,
            capture_output=True,
            check=True
        )
        
        # Create initial .gitignore if not exists
        gitignore_path = Path(project_path) / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/

# OS
.DS_Store
Thumbs.db
"""
            gitignore_path.write_text(gitignore_content)
        
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_shared_cache_dir() -> Path:
    """
    Get the path to the shared pip cache directory.
    
    This allows packages to be reused across projects without re-downloading.
    
    Returns:
        Path to the shared cache directory
    """
    cache_dir = Path.home() / ".pro-mgr" / "pip-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def create_venv(project_path: str, use_shared_cache: bool = True) -> Optional[Path]:
    """
    Create a virtual environment in the project.
    
    Args:
        project_path: Path to the project
        use_shared_cache: Whether to use shared pip cache for packages
    
    Returns:
        Path to the venv, or None if creation failed
    """
    venv_path = Path(project_path) / ".venv"
    
    try:
        subprocess.run(
            ["python", "-m", "venv", str(venv_path)],
            capture_output=True,
            check=True
        )
        
        # Configure pip to use shared cache
        if use_shared_cache:
            _configure_pip_cache(venv_path)
        
        return venv_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Try python3 if python doesn't work
        try:
            subprocess.run(
                ["python3", "-m", "venv", str(venv_path)],
                capture_output=True,
                check=True
            )
            
            # Configure pip to use shared cache
            if use_shared_cache:
                _configure_pip_cache(venv_path)
            
            return venv_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None


def _configure_pip_cache(venv_path: Path) -> None:
    """
    Configure pip in a venv to use the shared cache directory.
    
    This creates a pip.conf file in the venv that points to the shared cache.
    
    Args:
        venv_path: Path to the virtual environment
    """
    cache_dir = get_shared_cache_dir()
    
    # Create pip config directory
    if platform.system() == "Windows":
        pip_conf_dir = venv_path / "pip"
        pip_conf_file = pip_conf_dir / "pip.ini"
    else:
        pip_conf_dir = venv_path / "pip"
        pip_conf_file = pip_conf_dir / "pip.conf"
    
    pip_conf_dir.mkdir(parents=True, exist_ok=True)
    
    # Write pip config to use shared cache
    pip_conf_content = f"""[global]
cache-dir = {cache_dir}

[install]
cache-dir = {cache_dir}
"""
    pip_conf_file.write_text(pip_conf_content)


def get_venv_python(venv_path: str) -> Path:
    """
    Get the path to the Python executable in a venv.
    
    Args:
        venv_path: Path to the virtual environment
    
    Returns:
        Path to the python executable
    """
    venv = Path(venv_path)
    
    if platform.system() == "Windows":
        return venv / "Scripts" / "python.exe"
    else:
        return venv / "bin" / "python"


def detect_venv(project_path: str) -> Optional[Path]:
    """
    Try to detect an existing virtual environment in a project.
    
    Args:
        project_path: Path to the project
    
    Returns:
        Path to the detected venv, or None if not found
    """
    project = Path(project_path)
    
    # Common venv locations
    candidates = [
        project / ".venv",
        project / "venv",
        project / ".env",
        project / "env",
    ]
    
    for candidate in candidates:
        python_path = get_venv_python(str(candidate))
        if python_path.exists():
            return candidate
    
    return None


def create_project(
    name: str,
    template: str = "python-cli",
    path: str = ".",
    init_git_repo: bool = True,
    create_venv_env: bool = True,
    variables: dict = None
) -> dict:
    """
    Create a complete new project with all initializations.
    
    Args:
        name: Project name
        template: Template name
        path: Parent directory
        init_git_repo: Whether to initialize git
        create_venv_env: Whether to create venv
        variables: Template variables for substitution
    
    Returns:
        Dict with project info (path, venv_path, git_initialized)
    """
    # Create project structure with variables
    project_path = create_project_structure(name, template, path, variables)
    
    result = {
        'name': name,
        'path': str(project_path),
        'venv_path': None,
        'git_initialized': False,
    }
    
    # Initialize Git
    if init_git_repo:
        result['git_initialized'] = init_git(str(project_path))
    
    # Create virtual environment
    if create_venv_env:
        venv_path = create_venv(str(project_path))
        if venv_path:
            result['venv_path'] = str(venv_path)
    
    # Register in database
    db.add_project(
        name=name,
        root_path=str(project_path),
        venv_path=result['venv_path']
    )
    
    return result
