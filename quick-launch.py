#!/usr/bin/env python3
"""
🚀 Kimi-Dev-72B Quick Launcher
One-click access to your website and development environment
"""

import os
import sys
import webbrowser
import subprocess
import platform

def print_banner():
    print("🌐" + "="*50 + "🌐")
    print("      KIMI-DEV-72B QUICK LAUNCHER")
    print("🌐" + "="*50 + "🌐")
    print()

def print_menu():
    print("Choose your action:")
    print()
    print("1. 🌐 Open Live Website (https://nybbgll9qi.space.minimax.io)")
    print("2. 💻 Open in VSCode")
    print("3. 🚀 Start Development Environment")
    print("4. 📚 Open Documentation")
    print("5. 🔐 Show Login Credentials")
    print("6. 📁 Open Project Folder")
    print("7. 🐳 Start with Docker")
    print("8. ❌ Exit")
    print()

def open_live_website():
    print("🌐 Opening live website...")
    webbrowser.open('https://nybbgll9qi.space.minimax.io')
    print("✅ Website opened in your default browser")
    print("🔐 Admin Login: admin@secure-kimi.local / SecureKimi2024!")

def open_vscode():
    print("💻 Opening project in VSCode...")
    try:
        subprocess.run(['code', 'kimi-dev-workspace.code-workspace'], check=True)
        print("✅ VSCode opened with project workspace")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ VSCode not found. Please install VSCode or open manually:")
        print("   File: kimi-dev-workspace.code-workspace")

def start_dev_environment():
    print("🚀 Starting development environment...")
    try:
        if platform.system() == "Windows":
            subprocess.run(['dev-start.sh'], shell=True, check=True)
        else:
            subprocess.run(['bash', 'dev-start.sh'], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Development script not found or not executable")
        print("💡 Try running: chmod +x dev-start.sh")

def open_documentation():
    print("📚 Opening documentation...")
    if os.path.exists('README.md'):
        if platform.system() == "Darwin":  # macOS
            subprocess.run(['open', 'README.md'])
        elif platform.system() == "Windows":
            os.startfile('README.md')
        else:  # Linux
            subprocess.run(['xdg-open', 'README.md'])
        print("✅ Documentation opened")
    else:
        print("❌ README.md not found")

def show_credentials():
    print("🔐 Login Credentials:")
    print("="*30)
    print("🌐 Website: https://nybbgll9qi.space.minimax.io")
    print("📧 Email: admin@secure-kimi.local")
    print("🔑 Password: SecureKimi2024!")
    print("="*30)

def open_project_folder():
    print("📁 Opening project folder...")
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(['open', '.'])
        elif platform.system() == "Windows":
            subprocess.run(['explorer', '.'])
        else:  # Linux
            subprocess.run(['xdg-open', '.'])
        print("✅ Project folder opened")
    except Exception as e:
        print(f"❌ Could not open folder: {e}")

def start_docker():
    print("🐳 Starting with Docker...")
    try:
        subprocess.run(['docker-compose', 'up', '--build'], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found or docker-compose.yml missing")
        print("💡 Make sure Docker is installed and running")

def main():
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    while True:
        print_banner()
        print_menu()
        
        try:
            choice = input("Enter your choice (1-8): ").strip()
            print()
            
            if choice == '1':
                open_live_website()
            elif choice == '2':
                open_vscode()
            elif choice == '3':
                start_dev_environment()
            elif choice == '4':
                open_documentation()
            elif choice == '5':
                show_credentials()
            elif choice == '6':
                open_project_folder()
            elif choice == '7':
                start_docker()
            elif choice == '8':
                print("👋 Goodbye! Happy coding!")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter 1-8.")
            
            print()
            input("Press Enter to continue...")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye! Happy coding!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
