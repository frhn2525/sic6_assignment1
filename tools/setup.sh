#!/bin/bash
set -e

echo "===== SecurIn Devel - Development Environment Setup ====="

# Check required tools
echo "[1] Checking prerequisites..."
command -v git >/dev/null 2>&1 || { echo "Error: git is required but not installed. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required but not installed. Aborting."; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "Error: pip3 is required but not installed. Aborting."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Warning: docker is not installed. Container-based development will not be available."; }

# 
