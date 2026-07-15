from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "10_create_non_traumatic_sah_cohort.sql"
PYTHON_PATH = ROOT / "11_bigquery_notebook_non_traumatic_sah_analysis.py"


def wide_table_cases(sql: str) -> dict[str, str]:
    start = "CREATE OR REPLACE TABLE `mimic-study-498508.non_traumatic_sah_study.physiology_features_48h` AS"
    end = "FROM `mimic-study-498508.non_traumatic_sah_study.analysis_features_48h`;"
    segment = sql.split(start, 1)[1].split(end, 1)[0]
    return {
        alias: " ".join(body.split())
        for body, alias in re.findall(
            r"CASE\s+(.*?)\s+END AS ([a-z0-9_]+)", segment, flags=re.DOTALL
        )
    }


class SqlContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = SQL_PATH.read_text(encoding="utf-8")
        cls.cases = wide_table_cases(cls.sql)

    def test_primary_exclusion_is_preserved(self) -> None:
        body = self.cases["eligible_primary_analysis"]
        self.assertIn("core_feature_missing_count <= 2", body)
        self.assertIn("massive_transfusion_24h = 0", body)

    def test_inclusive_sensitivity_removes_only_massive_transfusion(self) -> None:
        body = self.cases["eligible_include_massive_transfusion_sensitivity"]
        self.assertEqual(
            body,
            "WHEN core_feature_missing_count <= 2 THEN 1 ELSE 0",
        )

    def test_sql_audit_outputs_include_sensitivity(self) -> None:
        self.assertIn(
            "COUNTIF(eligible_include_massive_transfusion_sensitivity = 1) "
            "AS include_massive_transfusion_sensitivity_rows",
            self.sql,
        )
        self.assertIn("10_sensitivity_include_massive_transfusion", self.sql)


class PythonContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PYTHON_PATH.read_text(encoding="utf-8")

    def test_python_loads_and_registers_sensitivity_flag(self) -> None:
        self.assertGreaterEqual(
            self.source.count('"eligible_include_massive_transfusion_sensitivity"'),
            2,
        )
        self.assertIn(
            '"include_massive_transfusion": '
            '"eligible_include_massive_transfusion_sensitivity"',
            self.source,
        )
        self.assertIn('COHORT_FLAG = "eligible_primary_analysis"', self.source)


class GovernanceContractTests(unittest.TestCase):
    def test_documents_preserve_exploratory_freeze_boundary(self) -> None:
        protocol = (ROOT / "protocol.md").read_text(encoding="utf-8")
        sap = (ROOT / "sap.md").read_text(encoding="utf-8")
        deviations = (ROOT / "deviations.md").read_text(encoding="utf-8")
        for document in (protocol, sap):
            self.assertIn("freeze_decision: DRAFT_BLOCKED", document)
            self.assertIn('outcome_access_before_freeze: "accessed"', document)
            self.assertIn("eligible_include_massive_transfusion_sensitivity", document)
        self.assertIn("DEV-2026-07-16-001", deviations)
        self.assertIn('outcome_access_before_decision: "accessed"', deviations)
        self.assertIn("不得描述为结果揭盲前预设", deviations)
        self.assertIn("支持性敏感性分析", protocol)
        self.assertIn("不用于估计 RBC 输血的因果效应", protocol)
        self.assertIn("支持性而非共同主要分析", sap)
        self.assertIn("不得据此估计 RBC 输血因果效应", sap)


if __name__ == "__main__":
    unittest.main()
