#!/bin/bash
set -e
sudo apt-get update && sudo apt-get install -y libgtk-3-dev clang cmake ninja-build pkg-config
sed -i 's/flet==0.24.1/flet>=0.25.2/g' requirements.txt
cat << 'EOF' > pyproject.toml
[project]
name = "hyper-ai-bot"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = ["flet>=0.25.2", "websockets", "pandas", "numpy", "scikit-learn"]

[tool.flet]
org = "com.hypervynx"
product = "HYPER AI BOT"

[tool.flet.android.permission]
"android.permission.INTERNET" = true
"android.permission.WAKE_LOCK" = true
EOF
