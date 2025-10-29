#!/usr/bin/env python3
"""
Test script for PDF and Image processing tools

This script verifies that the PDF and image analysis tools are working correctly.
Run it to ensure your setup is complete before using the agent.
"""

import os
import sys
from pathlib import Path

# Add my_agent to path
sys.path.insert(0, str(Path(__file__).parent))

from my_agent.tools.fetch_pdf import fetch_pdf
from my_agent.tools.analyze_image import analyze_image

def test_pdf_tool():
    """Test PDF processing tool."""
    print("=" * 60)
    print("Testing PDF Processing Tool")
    print("=" * 60)

    # Test with a publicly available PDF
    test_url = "https://arxiv.org/pdf/1706.03762.pdf"  # "Attention is All You Need" paper

    print(f"\n📄 Fetching PDF from: {test_url}")
    print("   (This is the famous 'Attention is All You Need' paper)")

    result = fetch_pdf(test_url, max_pages=2)  # Only first 2 pages for quick test

    if "error" in result and result["error"]:
        print(f"\n❌ ERROR: {result['error']}")
        return False

    print(f"\n✅ SUCCESS!")
    print(f"   Total pages in PDF: {result['total_pages']}")
    print(f"   Pages extracted: {result['extracted_pages']}")

    if result.get('metadata'):
        print(f"\n   Metadata:")
        for key, value in result['metadata'].items():
            print(f"      {key}: {value}")

    if result['pages']:
        first_page = result['pages'][0]
        print(f"\n   First page preview:")
        print(f"      Page number: {first_page['page_num']}")
        print(f"      Characters: {first_page['char_count']}")
        print(f"      Text preview: {first_page['text'][:150]}...")

    return True


def test_image_tool():
    """Test image analysis tool."""
    print("\n\n" + "=" * 60)
    print("Testing Image Analysis Tool")
    print("=" * 60)

    # Test with a publicly available image (a chart)
    test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Cat_August_2010-4.jpg/400px-Cat_August_2010-4.jpg"

    print(f"\n🖼️  Analyzing image from: {test_url}")
    print("   (Sample image from Wikimedia Commons)")

    result = analyze_image(test_url, question="What is in this image?", detail_level="medium")

    if "error" in result and result["error"]:
        print(f"\n❌ ERROR: {result['error']}")
        return False

    print(f"\n✅ SUCCESS!")
    print(f"   Description: {result['description']}")

    if result.get('objects'):
        print(f"\n   Objects detected: {', '.join(result['objects'])}")

    if result.get('text'):
        print(f"\n   Text detected: {result['text']}")

    print(f"\n   Full analysis:")
    print(f"      {result['details'][:300]}...")

    return True


def main():
    """Run all tests."""
    print("\n" + "🔬 " * 20)
    print("MULTIMODAL TOOLS TEST SUITE")
    print("🔬 " * 20 + "\n")

    # Check API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY not found in environment")
        print("   Please ensure your .env file is configured:")
        print("   1. cd my_agent")
        print("   2. Edit .env and add your GOOGLE_API_KEY")
        return

    print("✅ GOOGLE_API_KEY found\n")

    # Run tests
    pdf_success = test_pdf_tool()
    image_success = test_image_tool()

    # Summary
    print("\n\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"PDF Processing: {'✅ PASS' if pdf_success else '❌ FAIL'}")
    print(f"Image Analysis: {'✅ PASS' if image_success else '❌ FAIL'}")

    if pdf_success and image_success:
        print("\n🎉 All tests passed! Your multimodal tools are ready.")
        print("\nNext steps:")
        print("1. Start the ADK web interface: uv run adk web")
        print("2. Test with questions that need PDFs or images")
        print("3. Run evaluation: uv run python evaluate.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("- PyPDF2 not installed: run 'uv add PyPDF2'")
        print("- GOOGLE_API_KEY not set: check my_agent/.env")
        print("- Network issues: check internet connection")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
