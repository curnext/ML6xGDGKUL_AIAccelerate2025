"""
Setup script for Cited Web Research Assistant RAG system.
Run this after installing dependencies to verify everything works.
"""
import os
import sys


def check_dependencies():
    """Check if all required packages are installed."""
    print("Checking dependencies...")

    required = ["httpx", "trafilatura", "google"]
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: uv add httpx trafilatura")
        return False

    print("All dependencies installed!\n")
    return True


def check_env_file():
    """Check if .env file exists with required API keys."""
    print("Checking environment configuration...")

    env_path = os.path.join("my_agent", ".env")

    if not os.path.exists(env_path):
        print(f"  ✗ .env file not found at {env_path}")
        print("\nCreate .env file:")
        print("  1. cd my_agent")
        print("  2. copy .local_env .env")
        print("  3. Edit .env and add your API keys")
        return False

    print(f"  ✓ .env file exists")

    # Check for API keys (without reading actual values)
    with open(env_path, 'r') as f:
        content = f.read()

    has_google_key = "GOOGLE_API_KEY" in content and "your_actual_api_key_here" not in content
    has_serper_key = "SERPER_API_KEY" in content and "your_serper_api_key_here" not in content

    if has_google_key:
        print("  ✓ GOOGLE_API_KEY configured")
    else:
        print("  ✗ GOOGLE_API_KEY not configured")

    if has_serper_key:
        print("  ✓ SERPER_API_KEY configured")
    else:
        print("  ✗ SERPER_API_KEY not configured")
        print("\nGet Serper API key from: https://serper.dev")
        print("Free tier: 2,500 searches/month")

    if not (has_google_key and has_serper_key):
        return False

    print("Environment configured!\n")
    return True


def test_imports():
    """Test if agent and tools can be imported."""
    print("Testing imports...")

    try:
        from my_agent.agent import root_agent
        print("  ✓ Agent imported successfully")
    except Exception as e:
        print(f"  ✗ Failed to import agent: {e}")
        return False

    try:
        from my_agent.tools import web_search, fetch_url, compose_answer
        print("  ✓ Tools imported successfully")
    except Exception as e:
        print(f"  ✗ Failed to import tools: {e}")
        return False

    try:
        from my_agent.utils import (
            get_http_client,
            rank_search_results,
            extract_quotes_from_text,
            parse_date_to_iso,
            get_structured_logger
        )
        print("  ✓ Utils imported successfully")
    except Exception as e:
        print(f"  ✗ Failed to import utils: {e}")
        return False

    print("All imports successful!\n")
    return True


def test_basic_functionality():
    """Test basic functionality without making API calls."""
    print("Testing basic functionality...")

    try:
        from my_agent.utils.source_quality import get_source_quality_tier, SourceQualityTier
        from my_agent.utils.date_parser import parse_date_to_iso
        from my_agent.utils.quote_extractor import extract_quotes_from_text

        # Test source quality
        tier = get_source_quality_tier("https://sec.gov/test", True)
        assert tier == SourceQualityTier.TIER_1_PRIMARY
        print("  ✓ Source quality ranking works")

        # Test date parser
        date = parse_date_to_iso("2024-01-15")
        assert date == "2024-01-15"
        print("  ✓ Date parsing works")

        # Test quote extraction
        text = "This is a test sentence for quote extraction. It should work properly."
        quotes = extract_quotes_from_text(text, max_quotes=1)
        assert len(quotes) > 0
        print("  ✓ Quote extraction works")

    except Exception as e:
        print(f"  ✗ Functionality test failed: {e}")
        return False

    print("Basic functionality verified!\n")
    return True


def print_next_steps():
    """Print next steps for the user."""
    print("=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("\n1. Test interactively:")
    print("   uv run adk web")
    print("   Open: http://127.0.0.1:8000")
    print("\n2. Run benchmark evaluation:")
    print("   uv run python evaluate.py")
    print("\n3. Test specific question:")
    print("   uv run python evaluate.py --question 0")
    print("\n4. Read documentation:")
    print("   - IMPLEMENTATION_GUIDE.md (complete setup guide)")
    print("   - COST_ANALYSIS.md (cost optimization strategies)")
    print("\n5. Check logs:")
    print("   - Structured JSON logs show search decisions")
    print("   - Monitor latency, source quality, errors")
    print("\n" + "=" * 60)


def main():
    """Run all setup checks."""
    print("\n" + "=" * 60)
    print("CITED WEB RESEARCH ASSISTANT - SETUP VERIFICATION")
    print("=" * 60)
    print()

    # Run checks
    deps_ok = check_dependencies()
    env_ok = check_env_file()
    imports_ok = test_imports() if deps_ok else False
    func_ok = test_basic_functionality() if imports_ok else False

    # Summary
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    print(f"Dependencies:   {'✓ PASS' if deps_ok else '✗ FAIL'}")
    print(f"Environment:    {'✓ PASS' if env_ok else '✗ FAIL'}")
    print(f"Imports:        {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"Functionality:  {'✓ PASS' if func_ok else '✗ FAIL'}")

    if deps_ok and env_ok and imports_ok and func_ok:
        print("\n✓ ALL CHECKS PASSED!")
        print_next_steps()
        return 0
    else:
        print("\n✗ SETUP INCOMPLETE - Please fix issues above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
