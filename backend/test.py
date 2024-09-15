import subprocess


def test_pre_commit():
    # Run the pre-commit hook
    result = subprocess.run(
        ["pre-commit", "run", "--all-files"], capture_output=True, text=True
    )

    # Check the result
    if result.returncode == 0:
        print("Pre-commit hook passed!")
    else:
        print("Pre-commit hook failed. Please fix the issues before committing.")
        print(result.stdout)


if __name__ == "__main__":
    test_pre_commit()
