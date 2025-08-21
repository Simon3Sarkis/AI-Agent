import os
import subprocess

def run_python_file(working_directory, file_path, args=[]):
    try:
        abs_working_dir = os.path.abspath(working_directory)
        abs_target_path = os.path.abspath(os.path.join(abs_working_dir, file_path))

        if not abs_target_path.startswith(abs_working_dir):
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        if not os.path.isfile(abs_target_path):
            return f'Error: File "{file_path}" not found.'
        
        if not abs_target_path.endswith(".py"):
            return f'Error: "{file_path}" is not a Python file.'

        try:
            result = subprocess.run(
                ["python3", abs_target_path, *args],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=abs_working_dir
            )

            
            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            if result.returncode != 0:
                output += f"Process exited with code {result.returncode}\n"
            if not output.strip():
                output = "No output produced."

            return output

        except subprocess.TimeoutExpired:
            return f"Error: executing Python file: Timeout after 30 seconds."
        except Exception as e:
            return f"Error: executing Python file: {e}"

    except Exception as e:
        return f"Error: {str(e)}"