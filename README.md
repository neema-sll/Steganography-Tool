# 🔒 Secure Data Hider - Steganography Tool

[![Python Tests](https://github.com/neema-sll/Steganography-Tool/actions/workflows/python-tests.yml/badge.svg)](https://github.com/neema-sll/Steganography-Tool/actions/workflows/python-tests.yml)
[![CodeQL](https://github.com/neema-sll/Steganography-Tool/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/neema-sll/Steganography-Tool/actions/workflows/codeql-analysis.yml)
[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://img.shields.io/codecov/c/github/yourusername/steganography-tool)](https://codecov.io/gh/yourusername/steganography-tool)

A comprehensive steganography tool with GUI, CLI, encryption, and database persistence. Hide secret data within images using custom LSB (Least Significant Bit) algorithm with AES encryption.

## 📋 Table of Contents
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
  - [GUI Mode](#gui-mode)
  - [CLI Mode](#cli-mode)
- [Project Structure](#-project-structure)
- [Algorithm Details](#-algorithm-details)
- [Security Features](#-security-features)
- [Testing](#-testing)
- [Assessment Criteria](#-assessment-criteria)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### Core Functionality
- **Custom LSB Algorithm**: Proprietary steganography implementation (no built-in libraries)
- **Multiple Bit Support**: 1-3 bits per pixel for capacity vs. quality trade-off
- **AES-256 Encryption**: Secure data encryption before embedding
- **Data Compression**: Automatic compression for larger capacity
- **Multi-threading**: Optimized performance for large images

### Interfaces
- **🖥️ GUI Application**: Form-based Tkinter interface with 4 tabs
  - Encode tab: Hide data in images
  - Decode tab: Extract hidden data
  - History tab: View operation logs
  - Settings tab: Configure application

- **⌨️ CLI Interface**: Full command-line support for automation
  - Encode: `stegano-cli encode -i image.jpg -t "secret"`
  - Decode: `stegano-cli decode -i stego.png`
  - Capacity: `stegano-cli capacity -i image.jpg`
  - History: `stegano-cli history`
  - Integrity: `stegano-cli integrity -f file.png`

### Persistence & Security
- **SQLite Database**: Operation logging, session tracking, audit trails
- **File Integrity**: SHA-256 hashing for verification
- **Secure Key Storage**: OS-specific keychain integration
- **Session Management**: Track all operations with timestamps

### Testing & Quality
- **Unit Tests**: 100% test coverage for core modules
- **Integration Tests**: End-to-end workflow testing
- **CI/CD Pipeline**: Automated testing on GitHub Actions
- **Code Quality**: Linting, formatting, type checking

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Option 1: Install from source
```bash
# Clone the repository
git clone https://github.com/neema-sll/Steganography-Tool.git
cd steganography-tool

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .