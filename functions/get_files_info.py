import os
import google.genai.types as types

def get_files_info(working_directory, directory="."):
  
    full_path = os.path.abspath(os.path.join(working_directory, directory))
    working_directory_abs = os.path.abspath(working_directory)
    if not full_path.startswith(working_directory_abs):
        return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

    if not os.path.isdir(full_path):
        return f'Error: "{directory}" is not a directory'
    
    entries = []
    for name in sorted(os.listdir(full_path)):
        if name.startswith("__"):
            continue
        entry_path = os.path.join(full_path, name)
        size = os.path.getsize(entry_path)
        is_dir = os.path.isdir(entry_path)
        entries.append(f"- {name}: file_size={size} bytes, is_dir={is_dir}")

    return "\n".join(entries) if entries else "(empty directory)"

schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)