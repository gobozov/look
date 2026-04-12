#!/bin/bash

# Look - Installation Script
# This script installs 'look.py' as the 'lk' command on your system.

set -e # Exit immediately if a command fails

APP_NAME="lk"
SOURCE_FILE="look.py"
INSTALL_DIR="/usr/local/bin"
USER_INSTALL_DIR="$HOME/.local/bin"

echo "🚀 Installing Look as '$APP_NAME'..."

# 1. Check if source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "❌ Error: $SOURCE_FILE not found in the current directory."
    exit 1
fi

# 2. Make the script executable
chmod +x "$SOURCE_FILE"

# 3. Determine installation path
if [ -w "$INSTALL_DIR" ]; then
    # We have write access to /usr/local/bin
    cp "$SOURCE_FILE" "$INSTALL_DIR/$APP_NAME"
    echo "✅ Installed to $INSTALL_DIR/$APP_NAME"
elif [ -d "$USER_INSTALL_DIR" ] && [ -w "$USER_INSTALL_DIR" ]; then
    # We have write access to ~/.local/bin
    cp "$SOURCE_FILE" "$USER_INSTALL_DIR/$APP_NAME"
    echo "✅ Installed to $USER_INSTALL_DIR/$APP_NAME"
    
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$USER_INSTALL_DIR:"* ]]; then
        echo "⚠️  Note: $USER_INSTALL_DIR is not in your PATH. You may need to add it to your shell config (.bashrc/.zshrc)."
    fi
else
    # Fallback: Try with sudo
    echo "🔒 Admin privileges required to install to $INSTALL_DIR. Please enter your password if prompted."
    if sudo cp "$SOURCE_FILE" "$INSTALL_DIR/$APP_NAME"; then
        sudo chmod +x "$INSTALL_DIR/$APP_NAME"
        echo "✅ Installed to $INSTALL_DIR/$APP_NAME using sudo"
    else
        echo "❌ Installation failed. Please ensure you have the necessary permissions."
        exit 1
    fi
fi

echo ""
echo "✨ Installation Complete! You can now run the app by typing: $APP_NAME"
echo "📂 Use arrow keys to navigate and 'q' to quit."
