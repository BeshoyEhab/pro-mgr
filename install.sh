#!/bin/bash
#
# Pro-Mgr Installation Script
# This script installs pro-mgr and sets up shell completions
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default installation directory
DEFAULT_BIN_DIR="$HOME/.local/bin"
BIN_DIR="${PRO_MGR_BIN_DIR:-$DEFAULT_BIN_DIR}"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Pro-Mgr Installation Script      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for Python 3.10+
check_python() {
    echo -e "${YELLOW}Checking Python version...${NC}"
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
        
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
            return 0
        fi
    fi
    
    echo -e "${RED}✗ Python 3.10+ is required${NC}"
    exit 1
}

# Install the package
install_package() {
    echo
    echo -e "${YELLOW}Installing pro-mgr package...${NC}"
    
    cd "$SCRIPT_DIR"
    
    # Check if pipx is available (recommended for Arch/modern distros)
    if command -v pipx &> /dev/null; then
        echo -e "  Using ${BLUE}pipx${NC} for installation..."
        
        # Uninstall first if exists (to handle reinstalls)
        pipx uninstall pro-mgr 2>/dev/null || true
        
        # Install with pipx (regular install, not editable)
        # This copies files so the source folder can be deleted after install
        pipx install . --force
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Package installed successfully with pipx${NC}"
        else
            echo -e "${RED}✗ Failed to install package${NC}"
            exit 1
        fi
    else
        # Fallback: try pip with --user, or break-system-packages as last resort
        echo -e "  ${YELLOW}pipx not found, trying pip...${NC}"
        
        # Regular install (not editable) - copies files to site-packages
        if pip3 install --user . --quiet 2>/dev/null; then
            echo -e "${GREEN}✓ Package installed successfully with pip${NC}"
        elif pip3 install --user . --break-system-packages --quiet 2>/dev/null; then
            echo -e "${GREEN}✓ Package installed successfully with pip (--break-system-packages)${NC}"
        else
            echo -e "${RED}✗ Failed to install package${NC}"
            echo -e "${YELLOW}Tip: Install pipx with 'sudo pacman -S python-pipx' and try again${NC}"
            exit 1
        fi
    fi
}

# Ensure bin directory exists and is in PATH
setup_bin_directory() {
    echo
    echo -e "${YELLOW}Setting up binary directory...${NC}"
    
    # Create bin directory if it doesn't exist
    mkdir -p "$BIN_DIR"
    
    # Check if bin directory is in PATH
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo -e "${YELLOW}Note: $BIN_DIR is not in your PATH${NC}"
        echo -e "${YELLOW}Add this to your shell configuration:${NC}"
        echo -e "  ${GREEN}export PATH=\"\$PATH:$BIN_DIR\"${NC}"
    else
        echo -e "${GREEN}✓ $BIN_DIR is already in PATH${NC}"
    fi
    
    # Find where pip installed the script
    INSTALLED_BIN=$(python3 -c "import sys; print(f'{sys.prefix}/bin/pro-mgr')" 2>/dev/null || echo "")
    USER_BIN="$HOME/.local/bin/pro-mgr"
    
    # Check common locations for the installed script
    if [ -f "$USER_BIN" ]; then
        SOURCE_BIN="$USER_BIN"
    elif [ -f "$INSTALLED_BIN" ]; then
        SOURCE_BIN="$INSTALLED_BIN"
    else
        # Try to find it
        SOURCE_BIN=$(which pro-mgr 2>/dev/null || echo "")
    fi
    
    if [ -n "$SOURCE_BIN" ] && [ -f "$SOURCE_BIN" ]; then
        # Create symlink if needed
        if [ "$BIN_DIR/pro-mgr" != "$SOURCE_BIN" ]; then
            ln -sf "$SOURCE_BIN" "$BIN_DIR/pro-mgr" 2>/dev/null || true
        fi
        echo -e "${GREEN}✓ pro-mgr available at: $BIN_DIR/pro-mgr${NC}"
    else
        echo -e "${YELLOW}! Could not locate installed binary, but it should be available via pip${NC}"
    fi
}

# Setup shell completions
setup_completions() {
    echo
    echo -e "${YELLOW}Setting up shell completions...${NC}"
    
    # Detect current shell
    CURRENT_SHELL=$(basename "$SHELL")
    echo -e "  Detected shell: ${BLUE}$CURRENT_SHELL${NC}"
    
    # Bash completions
    setup_bash_completions
    
    # Zsh completions
    setup_zsh_completions
    
    # Fish completions
    setup_fish_completions
}

setup_bash_completions() {
    BASH_COMPLETION_DIR="$HOME/.local/share/bash-completion/completions"
    mkdir -p "$BASH_COMPLETION_DIR"
    
    # Generate Click completion script
    cat > "$BASH_COMPLETION_DIR/pro-mgr" << 'EOF'
# Bash completion for pro-mgr
# Generated by install.sh

_pro_mgr_completion() {
    local IFS=$'\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _PRO_MGR_COMPLETE=bash_complete pro-mgr 2>/dev/null)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"
        
        if [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        elif [[ $type == 'dir' ]]; then
            COMPREPLY+=($(compgen -d -- "$value"))
        elif [[ $type == 'file' ]]; then
            COMPREPLY+=($(compgen -f -- "$value"))
        fi
    done

    return 0
}

_pro_mgr_completion_setup() {
    complete -o nosort -F _pro_mgr_completion pro-mgr
}

_pro_mgr_completion_setup
EOF

    # Also add to .bashrc if not already there
    BASHRC="$HOME/.bashrc"
    COMPLETION_SOURCE="source \"$BASH_COMPLETION_DIR/pro-mgr\""
    
    if [ -f "$BASHRC" ]; then
        if ! grep -q "pro-mgr" "$BASHRC" 2>/dev/null; then
            echo "" >> "$BASHRC"
            echo "# Pro-Mgr shell completion" >> "$BASHRC"
            echo "[ -f \"$BASH_COMPLETION_DIR/pro-mgr\" ] && $COMPLETION_SOURCE" >> "$BASHRC"
        fi
    fi
    
    echo -e "${GREEN}  ✓ Bash completions installed${NC}"
}

setup_zsh_completions() {
    ZSH_COMPLETION_DIR="$HOME/.local/share/zsh/site-functions"
    mkdir -p "$ZSH_COMPLETION_DIR"
    
    # Generate Zsh completion script
    cat > "$ZSH_COMPLETION_DIR/_pro-mgr" << 'EOF'
#compdef pro-mgr
# Zsh completion for pro-mgr
# Generated by install.sh

_pro-mgr() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[pro-mgr] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _PRO_MGR_COMPLETE=zsh_complete pro-mgr 2>/dev/null)}")

    for key descr in ${(kv)response}; do
        if [[ "$descr" == "_" ]]; then
            completions+=("$key")
        else
            completions_with_descriptions+=("$key":"$descr")
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

compdef _pro-mgr pro-mgr
EOF

    # Add to fpath in .zshrc if not already
    ZSHRC="$HOME/.zshrc"
    if [ -f "$ZSHRC" ]; then
        if ! grep -q "pro-mgr" "$ZSHRC" 2>/dev/null; then
            echo "" >> "$ZSHRC"
            echo "# Pro-Mgr shell completion" >> "$ZSHRC"
            echo "fpath=($ZSH_COMPLETION_DIR \$fpath)" >> "$ZSHRC"
            echo "autoload -Uz compinit && compinit" >> "$ZSHRC"
        fi
    fi
    
    echo -e "${GREEN}  ✓ Zsh completions installed${NC}"
}

setup_fish_completions() {
    FISH_COMPLETION_DIR="$HOME/.config/fish/completions"
    mkdir -p "$FISH_COMPLETION_DIR"
    
    # Generate Fish completion script
    cat > "$FISH_COMPLETION_DIR/pro-mgr.fish" << 'EOF'
# Fish completion for pro-mgr
# Generated by install.sh

function _pro_mgr_completion
    set -l response (env _PRO_MGR_COMPLETE=fish_complete COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) pro-mgr 2>/dev/null)

    for completion in $response
        set -l metadata (string split "," -- $completion)

        if test $metadata[1] = "plain"
            echo $metadata[2]
        else if test $metadata[1] = "dir"
            __fish_complete_directories $metadata[2]
        else if test $metadata[1] = "file"
            __fish_complete_path $metadata[2]
        end
    end
end

complete -c pro-mgr -f -a "(_pro_mgr_completion)"

# Manual completions for main commands
complete -c pro-mgr -n "__fish_use_subcommand" -a "new" -d "Create a new project from template"
complete -c pro-mgr -n "__fish_use_subcommand" -a "init" -d "Initialize pro-mgr.toml in existing project"
complete -c pro-mgr -n "__fish_use_subcommand" -a "run" -d "Run a task for a project"
complete -c pro-mgr -n "__fish_use_subcommand" -a "shell" -d "Print shell activation command"
complete -c pro-mgr -n "__fish_use_subcommand" -a "project" -d "Manage registered projects"
complete -c pro-mgr -n "__fish_use_subcommand" -a "snip" -d "Manage code snippets"

# project subcommands
complete -c pro-mgr -n "__fish_seen_subcommand_from project" -a "list" -d "List all projects"
complete -c pro-mgr -n "__fish_seen_subcommand_from project" -a "info" -d "Show project info"
complete -c pro-mgr -n "__fish_seen_subcommand_from project" -a "add" -d "Register a project"
complete -c pro-mgr -n "__fish_seen_subcommand_from project" -a "rm" -d "Remove a project"
complete -c pro-mgr -n "__fish_seen_subcommand_from project" -a "update" -d "Update project"

# snip subcommands  
complete -c pro-mgr -n "__fish_seen_subcommand_from snip" -a "add" -d "Create a snippet"
complete -c pro-mgr -n "__fish_seen_subcommand_from snip" -a "ls" -d "List snippets"
complete -c pro-mgr -n "__fish_seen_subcommand_from snip" -a "search" -d "Search snippets"
complete -c pro-mgr -n "__fish_seen_subcommand_from snip" -a "show" -d "Show a snippet"
complete -c pro-mgr -n "__fish_seen_subcommand_from snip" -a "edit" -d "Edit a snippet"
complete -c pro-mgr -n "__fish_seen_subcommand_from snip" -a "rm" -d "Delete a snippet"
EOF
    
    echo -e "${GREEN}  ✓ Fish completions installed${NC}"
}

# Print summary
print_summary() {
    echo
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${GREEN}Installation complete!${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo
    echo -e "Binary location: ${GREEN}$BIN_DIR/pro-mgr${NC}"
    echo
    echo -e "Shell completions installed for:"
    echo -e "  • ${GREEN}Bash${NC}  → ~/.local/share/bash-completion/completions/pro-mgr"
    echo -e "  • ${GREEN}Zsh${NC}   → ~/.local/share/zsh/site-functions/_pro-mgr"
    echo -e "  • ${GREEN}Fish${NC}  → ~/.config/fish/completions/pro-mgr.fish"
    echo
    echo -e "${YELLOW}To start using pro-mgr:${NC}"
    echo -e "  1. Restart your shell or run: ${GREEN}source ~/.bashrc${NC} (or equivalent)"
    echo -e "  2. Test with: ${GREEN}pro-mgr --help${NC}"
    echo
    echo -e "${YELLOW}Quick start:${NC}"
    echo -e "  • Create a project:  ${GREEN}pro-mgr new my-app${NC}"
    echo -e "  • List projects:     ${GREEN}pro-mgr project list${NC}"
    echo -e "  • Open dashboard:    ${GREEN}pro-mgr${NC}"
    echo
}

# Uninstall function
uninstall() {
    echo -e "${YELLOW}Uninstalling pro-mgr...${NC}"
    
    # Remove pipx package (if installed via pipx)
    if command -v pipx &> /dev/null; then
        pipx uninstall pro-mgr 2>/dev/null || true
    fi
    
    # Remove pip package (if installed via pip)
    pip3 uninstall pro-mgr -y 2>/dev/null || true
    
    # Remove completions
    rm -f "$HOME/.local/share/bash-completion/completions/pro-mgr"
    rm -f "$HOME/.local/share/zsh/site-functions/_pro-mgr"
    rm -f "$HOME/.config/fish/completions/pro-mgr.fish"
    
    # Remove symlink
    rm -f "$BIN_DIR/pro-mgr"
    
    echo -e "${GREEN}✓ Uninstallation complete${NC}"
    echo -e "${YELLOW}Note: You may want to remove pro-mgr entries from your shell config files${NC}"
}

# Main
main() {
    case "${1:-}" in
        --uninstall|-u)
            uninstall
            exit 0
            ;;
        --help|-h)
            echo "Usage: ./install.sh [OPTIONS]"
            echo
            echo "Options:"
            echo "  --help, -h       Show this help message"
            echo "  --uninstall, -u  Uninstall pro-mgr"
            echo
            echo "Environment variables:"
            echo "  PRO_MGR_BIN_DIR  Custom binary directory (default: ~/.local/bin)"
            exit 0
            ;;
    esac
    
    check_python
    install_package
    setup_bin_directory
    setup_completions
    print_summary
}

main "$@"
