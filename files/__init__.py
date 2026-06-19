# files/__init__.py — File Operations Module

import os
import subprocess
import platform


def get_os():
    return platform.system()


def create_file(filename, content=""):
    """Create a file with given content."""
    try:
        if '.' not in filename:
            filename += '.txt'
        # Ensure parent directory exists
        parent = os.path.dirname(filename)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File '{filename}' created successfully."
    except Exception as e:
        return f"Error creating file: {str(e)}"


def open_file(filename):
    """Open a file with default application."""
    try:
        if not os.path.exists(filename):
            if not filename.endswith('.txt'):
                filename += '.txt'
        system = get_os()
        if system == "Windows":
            os.startfile(filename)
        elif system == "Darwin":
            subprocess.run(["open", filename])
        else:
            subprocess.run(["xdg-open", filename])
        return f"Opened file '{filename}'."
    except Exception as e:
        return f"Could not open file: {str(e)}"


def delete_file(filename):
    """Delete a file."""
    try:
        if not os.path.exists(filename):
            if not filename.endswith('.txt'):
                filename += '.txt'
        if os.path.exists(filename):
            os.remove(filename)
            return f"Deleted file '{filename}'."
        else:
            return f"File '{filename}' not found."
    except Exception as e:
        return f"Could not delete file: {str(e)}"


def list_files(directory="."):
    """List files in a directory."""
    try:
        items = os.listdir(directory)
        files = [f for f in items if os.path.isfile(os.path.join(directory, f))]
        dirs = [d for d in items if os.path.isdir(os.path.join(directory, d))]
        result = f"Directory: {os.path.abspath(directory)}\n"
        if dirs:
            result += f"Folders ({len(dirs)}): {', '.join(dirs[:20])}\n"
        if files:
            result += f"Files ({len(files)}): {', '.join(files[:20])}"
        return result
    except Exception as e:
        return f"Could not list directory: {str(e)}"


def read_file(filename):
    """Read and return file contents."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        if len(content) > 2000:
            return content[:2000] + "\n... (truncated)"
        return content
    except Exception as e:
        return f"Could not read file: {str(e)}"
