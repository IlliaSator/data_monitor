from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset


class EvidentlyRunner:
    def build_report(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        output_path: Path,
    ) -> dict:
        report = Report([DataDriftPreset()])
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            evaluation = report.run(current_data=current_data, reference_data=reference_data)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        evaluation.save_html(str(output_path))
        return evaluation.dict()
