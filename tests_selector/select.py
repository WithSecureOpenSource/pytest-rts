import subprocess

from tests_selector.helper import query_tests_sourcefile, get_test_lines_and_update_lines


def run():
    # runs changed tests + tests that are related to changes in source files
    git_data = str(
        subprocess.run(
            ["git", "diff", "-U0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).stdout
    )
    test_lines, updates_to_lines = get_test_lines_and_update_lines(git_data)
    tests = query_tests_sourcefile(test_lines, src_id)


def main():
    run()


if __name__ == "__main__":
    main()
