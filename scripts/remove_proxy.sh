#!/bin/bash

echo "Removing proxy settings..."

# Unset proxy environment variables
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy
unset NO_PROXY
unset no_proxy

echo ""
echo "✓ Proxy variables cleared for current session."
echo ""
echo "To remove permanently:"
echo ""
echo "1. Edit your shell configuration file:"
echo "   - For bash: ~/.bashrc or ~/.bash_profile"
echo "   - For zsh: ~/.zshrc"
echo "   - For system-wide: /etc/environment"
echo ""
echo "2. Remove or comment out these lines:"
echo "   export HTTP_PROXY=..."
echo "   export HTTPS_PROXY=..."
echo "   export http_proxy=..."
echo "   export https_proxy=..."
echo ""
echo "3. Apply changes:"
echo "   source ~/.bashrc  (or your shell config file)"
echo ""
echo "Or run this command to remove from current user's bashrc:"
echo "sed -i '/HTTP_PROXY/d; /HTTPS_PROXY/d; /http_proxy/d; /https_proxy/d' ~/.bashrc"
echo ""