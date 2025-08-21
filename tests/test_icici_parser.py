import sys, os
import pandas as pd

# ✅ Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from custom_parsers.icici_parser import parse


def test_icici_parser():
    pdf_path = os.path.join(BASE_DIR, "data", "icici", "icic_sample.pdf")
    csv_path = os.path.join(BASE_DIR, "data", "icici", "icic_sample.csv")

    result_df = parse(pdf_path)
    expected_df = pd.read_csv(csv_path)

    # ✅ Ensure both dataframes have same shape and content
    pd.testing.assert_frame_equal(
        result_df.reset_index(drop=True),
        expected_df.reset_index(drop=True),
        check_dtype=False
    )
