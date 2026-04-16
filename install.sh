#!/bin/bash

# Look - Installation Script
# This script installs 'look.py' as the 'lk' command with CD-on-exit support.

set -e

APP_NAME="lk"
BINARY_NAME="lk-bin"
SOURCE_FILE="look.py"
INSTALL_DIR="/usr/local/bin"

echo "🚀 Installing Look..."

# 1. Make the source executable
chmod +x "$SOURCE_FILE"

# 2. Install the binary
if [ -w "$INSTALL_DIR" ]; then
    cp "$SOURCE_FILE" "$INSTALL_DIR/$BINARY_NAME"
    echo "✅ Binary installed to $INSTALL_DIR/$BINARY_NAME"
else
    echo "🔒 Admin privileges required. Please enter password if prompted."
    sudo cp "$SOURCE_FILE" "$INSTALL_DIR/$BINARY_NAME"
    sudo chmod +x "$INSTALL_DIR/$BINARY_NAME"
    echo "✅ Binary installed to $INSTALL_DIR/$BINARY_NAME using sudo"
fi

# 3. Create the shell wrapper function
WRAPPER_FUNC="
# Look - File Explorer Wrapper
lk() {
    $BINARY_NAME \"\$@\"
    if [ -f /tmp/lk-cwd ]; then
        cd \"\$(cat /tmp/lk-cwd)\"
        rm /tmp/lk-cwd
    fi
}
"

# 4. Determine shell config file
SHELL_CONFIG=""
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    if [ -f "$HOME/.bash_profile" ]; then
        SHELL_CONFIG="$HOME/.bash_profile"
    else
        SHELL_CONFIG="$HOME/.bashrc"
    fi
fi

# 5. Add wrapper to config if it doesn't exist
if [ -n "$SHELL_CONFIG" ]; then
    if ! grep -q "lk()" "$SHELL_CONFIG"; then
        echo "$WRAPPER_FUNC" >> "$SHELL_CONFIG"
        echo "✅ Added shell wrapper to $SHELL_CONFIG"
        echo "🔄 Please run 'source $SHELL_CONFIG' or restart your terminal."
    else
        echo "ℹ️  Shell wrapper already exists in $SHELL_CONFIG"
    fi
else
    echo "⚠️  Could not detect your shell config file. Please manually add this to your .zshrc or .bashrc:"
    echo "$WRAPPER_FUNC"
fi

echo ""
echo "✨ Installation Complete!"
echo "👉 Use 'lk' to launch the explorer. It will now track your location on exit!"
