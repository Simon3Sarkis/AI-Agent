import os
import sys
import json
from dotenv import load_dotenv
from google import genai
import google.genai.types as types
from functions.get_files_info import schema_get_files_info, get_files_info
from functions.get_file_content import schema_get_file_content, get_file_content
from functions.run_python import schema_run_python_file, run_python_file
from functions.write_files import schema_write_file, write_file

available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
    ]
)

system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""
configs = types.GenerateContentConfig(
    tools=[available_functions], system_instruction=system_prompt
)
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

if len(sys.argv) < 2:
    sys.exit(1)

prompt = sys.argv[1]
verbose = "--verbose" in sys.argv

messages = [
    types.Content(role="user", parts=[types.Part(text=prompt)]),
]

response = client.models.generate_content(
    model="gemini-2.0-flash-001",
    contents=messages,
    config=configs,
)

# ---------------------------
# Map schema names to functions
# ---------------------------
FUNCTIONS = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file,
}

# ---------------------------
# Function dispatcher
# ---------------------------
def call_function(function_call_part, verbose=False):
    function_name = function_call_part.name
    args = dict(function_call_part.args)

    # Inject working directory
    args["working_directory"] = "./calculator"

    if verbose:
        print(f"Calling function: {function_name}({args})")
    else:
        print(f" - Calling function: {function_name}")

    if function_name not in FUNCTIONS:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )

    try:
        function_result = FUNCTIONS[function_name](**args)
    except Exception as e:
        function_result = f"Exception during call: {e}"

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": function_result},
            )
        ],
    )

# ---------------------------
# Handle function call from LLM
# ---------------------------
if response.function_calls:
    function_call_part = response.function_calls[0]
    function_call_result = call_function(function_call_part, verbose=verbose)

    if not function_call_result.parts or not function_call_result.parts[0].function_response.response:
        raise RuntimeError("Function call failed: no response in function_response")

    if verbose:
        print(f"-> {function_call_result.parts[0].function_response.response}")
else:
    print(response.text)

# ---------------------------
# Verbose logging
# ---------------------------
if verbose:
    print(f"\nUser prompt: {prompt}")
    print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Response tokens: {response.usage_metadata.candidates_token_count}")
