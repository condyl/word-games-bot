#!/usr/bin/env python3
import os
import sys
import subprocess

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_test(test_file):
    """Run a test file and return True if it passes, False otherwise."""
    print(f"\n{'='*50}")
    print(f"Running {test_file}")
    print(f"{'='*50}")
    
    result = subprocess.run(['python3', test_file], capture_output=False)
    return result.returncode == 0

def main():
    """Run all test files in the tests directory."""
    # Get the directory of this script
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get all Python files in the tests directory that start with "test_"
    test_files = [f for f in os.listdir(tests_dir) 
                 if f.startswith('test_') and f.endswith('.py')]
    
    # Sort the test files alphabetically
    test_files.sort()
    
    # Print the list of tests that will be run
    print(f"Found {len(test_files)} tests to run:")
    for test_file in test_files:
        if test_file != os.path.basename(__file__):
            print(f"  - {test_file}")
    
    # Run each test file
    passed = 0
    failed = 0
    
    for test_file in test_files:
        # Skip this script
        if test_file == os.path.basename(__file__):
            continue
            
        test_path = os.path.join(tests_dir, test_file)
        if run_test(test_path):
            passed += 1
        else:
            failed += 1
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 