"""
测试运行脚本
方便运行各种测试
"""
import subprocess
import sys
import argparse


def run_unit_tests():
    """运行单元测试"""
    print("=" * 60)
    print("Running Unit Tests")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/", "-v"],
        cwd="d:\\Project\\Novel Agent Studio\\backend"
    )
    return result.returncode


def run_integration_tests():
    """运行集成测试"""
    print("=" * 60)
    print("Running Integration Tests")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/integration/", "-v"],
        cwd="d:\\Project\\Novel Agent Studio\\backend"
    )
    return result.returncode


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Running All Tests")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd="d:\\Project\\Novel Agent Studio\\backend"
    )
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run Novel Agent Studio tests")
    parser.add_argument(
        "--unit", "-u",
        action="store_true",
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration", "-i",
        action="store_true",
        help="Run integration tests only"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all tests (default)"
    )

    args = parser.parse_args()

    if args.unit:
        return run_unit_tests()
    elif args.integration:
        return run_integration_tests()
    else:
        return run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
