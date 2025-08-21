from functions.get_files_info import get_files_info
from functions.get_file_content import get_file_content
from functions.write_files import write_file

def run_tests():
    print(write_file("calculator", "lorem.txt", "wait, this isn't lorem ipsum"))
    print(write_file("calculator", "pkg/morelorem.txt", "lorem ipsum dolor sit amet"))
    print(write_file("calculator", "/tmp/temp.txt", "this should not be allowed"))
if __name__ == "__main__":
    run_tests()
