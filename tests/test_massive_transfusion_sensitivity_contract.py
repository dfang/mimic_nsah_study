import ast
from pathlib import Path
import re
import unittest

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "10_create_non_traumatic_sah_cohort.sql"
PYTHON_PATH = ROOT / "11_bigquery_notebook_non_traumatic_sah_analysis.py"


def load_sensitivity_production_namespace() -> dict:
    """Load only sensitivity production constants/helpers, never notebook I/O/main."""
    tree = ast.parse(PYTHON_PATH.read_text(encoding="utf-8"), filename=str(PYTHON_PATH))
    constant_names = {
        "PRIMARY_K",
        "RANDOM_SEED",
        "COHORT_FLAG",
        "FEATURES",
        "SEVERITY_DIRECTIONS",
        "SENSITIVITY_COHORT_FLAGS",
    }
    helper_names = {
        "preprocess_feature_matrix",
        "build_ordered_phenotype_labels",
        "build_assignments",
        "run_sensitivity_cohort_summaries",
    }
    selected_nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in constant_names
            for target in node.targets
        ):
            selected_nodes.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in helper_names:
            selected_nodes.append(node)

    module = ast.Module(body=selected_nodes, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "np": np,
        "pd": pd,
        "KMeans": KMeans,
        "SimpleImputer": SimpleImputer,
        "StandardScaler": StandardScaler,
        "adjusted_rand_score": adjusted_rand_score,
        "silhouette_score": silhouette_score,
    }
    exec(compile(module, str(PYTHON_PATH), "exec"), namespace)
    return namespace


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
        self.assertIn(
            'ANALYSIS_SUPERSET_FLAG = "eligible_include_massive_transfusion_sensitivity"',
            self.source,
        )
        self.assertIn("WHERE {ANALYSIS_SUPERSET_FLAG} = 1", self.source)
        self.assertIn("analysis_df = read_table_from_bigquery()", self.source)
        self.assertIn(
            "df = analysis_df[analysis_df[COHORT_FLAG] == 1].copy()",
            self.source,
        )
        self.assertRegex(
            self.source,
            r'run_sensitivity_cohort_summaries\(\s*analysis_df,\s*primary\["assignments"\]\s*,?\s*\)',
        )

    def test_sensitivity_summary_reports_overlap_profiles_centers_and_flag(self) -> None:
        namespace = load_sensitivity_production_namespace()
        features = namespace["FEATURES"]
        rows = []
        stay_id = 1
        for cluster, center in enumerate((-4.0, 0.0, 4.0)):
            for member in range(25):
                jitter = (member - 12) / 100.0
                row = {
                    "stay_id": stay_id,
                    "hospital_mortality": int(cluster == 2 and member % 3 == 0),
                    "early_anemia_all": int(cluster > 0),
                    "eligible_include_massive_transfusion_sensitivity": 1,
                }
                row.update(
                    {
                        feature: center + jitter + feature_index / 1000.0
                        for feature_index, feature in enumerate(features)
                    }
                )
                rows.append(row)
                stay_id += 1

        sensitivity_df = pd.DataFrame(rows)
        primary_df = sensitivity_df.groupby(
            pd.cut(sensitivity_df[features[0]], bins=[-np.inf, -2, 2, np.inf], labels=False)
        ).head(20)
        primary_assignments = primary_df[["stay_id"]].copy()
        primary_assignments["phenotype"] = np.repeat([1, 2, 3], 20)

        result = namespace["run_sensitivity_cohort_summaries"](
            sensitivity_df,
            primary_assignments,
        )

        self.assertEqual(
            set(result["cohort_flag"]),
            {"eligible_include_massive_transfusion_sensitivity"},
        )
        self.assertEqual(set(result["primary_overlap_n"]), {len(primary_assignments)})
        self.assertTrue(result["ari_vs_primary_subset"].notna().all())
        self.assertTrue(np.isfinite(result["ari_vs_primary_subset"]).all())
        for feature in features:
            self.assertTrue(result[f"{feature}_mean"].notna().all())
            self.assertTrue(result[f"{feature}_standardized_center"].notna().all())

    def test_too_small_sensitivity_uses_actual_flag_and_overlap_count(self) -> None:
        namespace = load_sensitivity_production_namespace()
        features = namespace["FEATURES"]
        sensitivity_df = pd.DataFrame(
            [
                {
                    "stay_id": stay_id,
                    "hospital_mortality": 0,
                    "early_anemia_all": 0,
                    "eligible_include_massive_transfusion_sensitivity": 1,
                    **{feature: float(stay_id) for feature in features},
                }
                for stay_id in range(1, 11)
            ]
        )
        primary_assignments = pd.DataFrame(
            {"stay_id": range(1, 7), "phenotype": [1, 1, 2, 2, 3, 3]}
        )

        result = namespace["run_sensitivity_cohort_summaries"](
            sensitivity_df,
            primary_assignments,
        )

        self.assertEqual(
            result.loc[0, "cohort_flag"],
            "eligible_include_massive_transfusion_sensitivity",
        )
        self.assertEqual(result.loc[0, "primary_overlap_n"], 6)
        self.assertTrue(pd.isna(result.loc[0, "ari_vs_primary_subset"]))
        for feature in features:
            self.assertTrue(pd.isna(result.loc[0, f"{feature}_mean"]))
            self.assertTrue(pd.isna(result.loc[0, f"{feature}_standardized_center"]))


class GovernanceContractTests(unittest.TestCase):
    def test_documents_preserve_exploratory_freeze_boundary(self) -> None:
        protocol = (ROOT / "protocol.md").read_text(encoding="utf-8")
        sap = (ROOT / "sap.md").read_text(encoding="utf-8")
        deviations = (ROOT / "deviations.md").read_text(encoding="utf-8")
        for document in (protocol, sap):
            self.assertIn("freeze_decision: DRAFT_BLOCKED", document)
            self.assertIn('outcome_access_before_freeze: "accessed"', document)
            self.assertIn("eligible_include_massive_transfusion_sensitivity", document)
            self.assertIn("七项核心", document)
            self.assertIn("七维标准化空间直接运行 K-means", document)
        self.assertIn('version: "0.1.2"', protocol)
        self.assertIn('sap_version: "0.1.2"', sap)
        self.assertIn('protocol_version: "0.1.2"', sap)
        self.assertIn(
            'primary_algorithm: "seven core features; median imputation; '
            'Z-score standardization; direct K-means in seven-dimensional scaled space (K=3)"',
            sap,
        )
        self.assertIn("DEV-2026-07-16-001", deviations)
        self.assertIn("DEV-2026-07-16-002", deviations)
        self.assertIn('outcome_access_before_decision: "accessed"', deviations)
        self.assertIn("不得描述为结果揭盲前预设", deviations)
        self.assertIn("支持性敏感性分析", protocol)
        self.assertIn("不用于估计 RBC 输血的因果效应", protocol)
        self.assertIn("支持性而非共同主要分析", sap)
        self.assertIn("不得据此估计 RBC 输血因果效应", sap)

        massive_transfusion_section = sap.split(
            "### 13.1 不排除大量输血敏感性分析契约", 1
        )[1].split("## 14.", 1)[0]
        self.assertNotIn("PCA", massive_transfusion_section)
        self.assertIn("原始特征谱", massive_transfusion_section)
        self.assertIn("标准化中心", massive_transfusion_section)
        self.assertIn("重叠 ARI", massive_transfusion_section)

    def test_python_constructs_sensitivity_governance_fields(self) -> None:
        source = PYTHON_PATH.read_text(encoding="utf-8")
        self.assertIn('"cohort_flag": flag_col', source)
        self.assertIn('"primary_overlap_n": int(len(overlap))', source)
        self.assertIn('row[f"{feature}_mean"]', source)
        self.assertIn('row[f"{feature}_standardized_center"]', source)


if __name__ == "__main__":
    unittest.main()
