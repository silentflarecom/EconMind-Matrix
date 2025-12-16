# Layer 3 Tests

This directory contains integration and unit tests for the Layer 3 Sentiment module.

## Running the System Test

The `test_workflow.py` script simulates the entire Layer 3 pipeline without requiring external API keys.

1. Navigate to the project root:
   ```bash
   cd d:\Github\EconMind-Matrix
   ```

2. Run the test script:
   ```bash
   python layer3-sentiment/tests/test_workflow.py
   ```

## What is Tested?

- **Database Initialization**: Creates `test_layer3.db` and tables.
- **Article Insertion**: Simulates news crawling and storage.
- **Search**: Verifies full-text search.
- **Annotation**: Runs rule-based sentiment analysis.
- **Trend Analysis**: Calculates trends from the annotated data.
- **Import Logic**: Verifies that the nested package structure works correctly.
