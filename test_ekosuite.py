import sys
import pytest

def main():
    pytest.main(["-v", "tests/"])
    sys.exit()

if __name__ == "__main__":
    main()