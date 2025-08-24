import os
import sys
from dotenv import load_dotenv
from google import genai
import google.genai.types as types

from functions.get_files_info import schema_get_files_info, get_files_info
from functions.get_file_content import schema_get_file_content, get_file_content
from functions.run_python import schema_run_python_file, run_python_file
from functions.write_files import schema_write_file, write_file

# ---------------------------
# Setup
# ---------------------------
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

When a user asks a question or makes a request, make a function call plan. 
You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. 
You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
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

# ---------------------------
# Conversation state
# ---------------------------
messages = [
    types.Content(role="user", parts=[types.Part(text=prompt)]),
]

# ---------------------------
# Function dispatcher
# ---------------------------
FUNCTIONS = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file,
}

def call_function(function_call_part, verbose=False):
    function_name = function_call_part.name
    args = dict(function_call_part.args)

    # Inject working directory for safety
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
# Feedback loop (the "Agent")
# ---------------------------
MAX_ITERS = 20

for i in range(MAX_ITERS):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=messages,
            config=configs,
        )

        if not response.candidates:
            print("No candidates returned, stopping.")
            break

        candidate = response.candidates[0]

        # Append model response into messages
        messages.append(types.Content(role="model", parts=candidate.content.parts))

        # Separate text vs function calls
        function_calls = [part.function_call for part in candidate.content.parts if part.function_call]
        final_texts = [part.text for part in candidate.content.parts if part.text]

        if function_calls:
            # Execute each tool call
            for fc in function_calls:
                function_call_result = call_function(fc, verbose=verbose)
                messages.append(function_call_result)
                if verbose and function_call_result.parts:
                    print(f"-> {function_call_result.parts[0].function_response.response}")
        elif final_texts:
            # No tool calls, just text → final response
            print("\nFinal response:\n")
            print("\n".join(final_texts))
            break

    except Exception as e:
        print(f"Error during loop: {e}")
        break
else:
    print("Max iterations reached without final response.")


# ---------------------------
# Verbose logging
# ---------------------------
if verbose and "response" in locals() and response.usage_metadata:
    print(f"\nUser prompt: {prompt}")
    print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Response tokens: {response.usage_metadata.candidates_token_count}")
