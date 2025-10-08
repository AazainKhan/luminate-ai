"""
Master test runner - Run all test suites and generate comprehensive report
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Test files to run
TEST_FILES = [
    "test_auto_mode_router.py",
    "test_educate_graph.py",
    "test_navigate_brief_summary.py",
    "test_agent_traces.py",
    "test_interactive_formatting.py"
]

def run_test_file(test_file):
    """Run a single test file and return result"""
    test_path = Path(__file__).parent / test_file
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "name": test_file,
            "passed": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "name": test_file,
            "passed": False,
            "output": "",
            "error": "Test timeout (30s)"
        }
    except Exception as e:
        return {
            "name": test_file,
            "passed": False,
            "output": "",
            "error": str(e)
        }


def main():
    """Run all tests and generate report"""
    print("="*70)
    print("LUMINATE AI - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Running {len(TEST_FILES)} test suites...\n")
    
    results = []
    
    for test_file in TEST_FILES:
        print(f"\n{'='*70}")
        print(f"Running: {test_file}")
        print(f"{'='*70}")
        
        result = run_test_file(test_file)
        results.append(result)
        
        # Print output
        if result["output"]:
            print(result["output"])
        
        if result["error"] and not result["passed"]:
            print(f"\nERROR OUTPUT:")
            print(result["error"])
        
        # Status
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"\n{status}: {test_file}")
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    
    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status}: {result['name']}")
    
    print(f"\n{'='*70}")
    print(f"Total: {passed_count}/{total_count} test suites passed")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    # Generate report file
    report_path = Path(__file__).parent / "test_results.txt"
    with open(report_path, 'w') as f:
        f.write("LUMINATE AI - TEST RESULTS\n")
        f.write("="*70 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Test Suites: {total_count}\n")
        f.write(f"Passed: {passed_count}\n")
        f.write(f"Failed: {total_count - passed_count}\n\n")
        
        for result in results:
            f.write(f"\n{'='*70}\n")
            f.write(f"Test Suite: {result['name']}\n")
            f.write(f"Status: {'PASSED' if result['passed'] else 'FAILED'}\n")
            f.write(f"{'='*70}\n")
            f.write(result['output'])
            if result['error']:
                f.write(f"\nErrors:\n{result['error']}\n")
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Exit with appropriate code
    sys.exit(0 if passed_count == total_count else 1)


if __name__ == "__main__":
    main()

