from functions.get_files_info import get_files_info
from functions.get_file_content import get_file_content
from functions.write_files import write_file
from functions.run_python import run_python_file

def run_tests():
    print(run_python_file("calculator", "main.py"))
    print(run_python_file("calculator", "main.py", ["3 + 5"]))
    print(run_python_file("calculator", "tests.py"))
    print(run_python_file("calculator", "../main.py"))
    print(run_python_file("calculator", "nonexistent.py"))
if __name__ == "__main__":
    run_tests()
