> Note: This is a historical result export from the earlier phenotype run that used `gcs_motor_min_48h` as the neural clustering variable. The current extraction and analysis strategy uses `gcs_min_48h` / `gcs_grade_min_48h` for primary clustering and keeps `gcs_motor_min_48h` for sensitivity or prediction comparison. Re-run the SQL and Python analysis before using this file as current evidence.

读取 BigQuery 表：mimic-study-498508.ash_study.physiology_features_48h
当前 cohort flag：eligible_primary_analysis = 1
读取完成：229 行，29 列

总体样本快速检查：

    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }





      cohort_flag
      n
      hospital_deaths
      hospital_mortality_rate
      early_anemia_n
      early_anemia_rate
      any_rbc_transfusion_48h_rate




      0
      eligible_primary_analysis
      229
      32
      0.139738
      57
      0.248908
      0.008734















    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }



      const buttonEl =
        document.querySelector('#df-ac5323f6-a1a3-40c3-9c32-2e4a79b2665e button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-ac5323f6-a1a3-40c3-9c32-2e4a79b2665e');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }










    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }





      feature
      missing_n
      total_n
      missing_rate




      4
      lactate_max_48h
      110
      229
      0.480349


      5
      spo2_fio2_min_48h
      87
      229
      0.379913


      3
      shock_index_max_48h
      23
      229
      0.100437


      2
      map_min_48h
      9
      229
      0.039301


      0
      hb_min_48h_all
      0
      229
      0.000000


      1
      gcs_motor_min_48h
      0
      229
      0.000000


      6
      creatinine_max_48h
      0
      229
      0.000000


      7
      platelet_min_48h
      0
      229
      0.000000















    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }



      const buttonEl =
        document.querySelector('#df-ad6e2d86-3542-465e-9e67-83a6d3d42dc3 button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-ad6e2d86-3542-465e-9e67-83a6d3d42dc3');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }










    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }





      cohort_flag
      k
      inertia
      silhouette
      calinski_harabasz
      davies_bouldin
      min_cluster_n
      min_cluster_frac
      max_cluster_n




      0
      eligible_primary_analysis
      2
      1555.248546
      0.156069
      40.393917
      2.114423
      96
      0.419214
      133


      1
      eligible_primary_analysis
      3
      1369.933529
      0.177433
      38.113901
      1.875437
      56
      0.244541
      111


      2
      eligible_primary_analysis
      4
      1245.039913
      0.161620
      35.357908
      1.801768
      48
      0.209607
      71


      3
      eligible_primary_analysis
      5
      1124.707749
      0.182760
      35.216585
      1.617654
      8
      0.034934
      78















    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }



      const buttonEl =
        document.querySelector('#df-df920f72-e014-41fb-a7f0-aef7d369d2ea button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-df920f72-e014-41fb-a7f0-aef7d369d2ea');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }

写回 BigQuery：mimic-study-498508.ash_study.phenotype_k_selection_metrics (4 行)

最终用于聚类的 K = 4

K-means 原始 cluster 到 phenotype 严重程度排序映射：

    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }





      raw_cluster
      phenotype




      0
      3
      1


      1
      1
      2


      2
      0
      3


      3
      2
      4















    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }



      const buttonEl =
        document.querySelector('#df-71da4f4e-84e4-4605-83bc-c4ddcd7e60c7 button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-71da4f4e-84e4-4605-83bc-c4ddcd7e60c7');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }

标准化 cluster center：

    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }





      cohort_flag
      raw_cluster
      hb_min_48h_all
      gcs_motor_min_48h
      map_min_48h
      shock_index_max_48h
      lactate_max_48h
      spo2_fio2_min_48h
      creatinine_max_48h
      platelet_min_48h
      severity_score
      phenotype




      3
      eligible_primary_analysis
      3
      0.317195
      1.153813
      -0.310168
      -0.095998
      -0.302209
      -0.270318
      -0.235811
      0.393588
      -1.918126
      1


      1
      eligible_primary_analysis
      1
      0.378815
      -0.462693
      1.159809
      -0.579927
      -0.152567
      -0.400783
      -0.203001
      -0.012838
      -1.597807
      2


      0
      eligible_primary_analysis
      0
      -0.252828
      -0.739465
      -0.026662
      0.243752
      -0.204276
      1.526998
      -0.264012
      -0.260865
      -0.471714
      3


      2
      eligible_primary_analysis
      2
      -0.640962
      -0.729134
      -0.591053
      0.486900
      0.820743
      -0.587538
      0.817492
      -0.380087
      5.053910
      4















    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }



      const buttonEl =
        document.querySelector('#df-d031924d-cab6-47c9-a34f-36cdf8d5f614 button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-d031924d-cab6-47c9-a34f-36cdf8d5f614');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }

Phenotype 结局汇总：

    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }





      cohort_flag
      phenotype
      n
      hospital_deaths
      hospital_mortality_rate
      icu_deaths
      icu_mortality_rate
      early_anemia_n
      early_anemia_rate
      age_median
      icu_los_days_median
      hospital_los_days_median
      any_rbc_transfusion_48h_rate




      0
      eligible_primary_analysis
      1
      82
      1
      0.012195
      0
      0.000000
      11
      0.134146
      50.0
      6.979167
      11.645833
      0.012195


      1
      eligible_primary_analysis
      2
      49
      8
      0.163265
      8
      0.163265
      6
      0.122449
      56.0
      13.041667
      14.833333
      0.000000


      2
      eligible_primary_analysis
      3
      47
      7
      0.148936
      6
      0.127660
      15
      0.319149
      56.0
      14.583333
      20.458333
      0.000000


      3
      eligible_primary_analysis
      4
      51
      16
      0.313725
      12
      0.235294
      25
      0.490196
      65.0
      12.916667
      16.500000
      0.019608















    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }



      const buttonEl =
        document.querySelector('#df-4823a22c-c143-4a85-8a53-9b40ad25e48c button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-4823a22c-c143-4a85-8a53-9b40ad25e48c');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }

Phenotype x anemia 可行性表：

    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }





      cohort_flag
      phenotype
      early_anemia_all
      n
      deaths
      mortality_rate




      0
      eligible_primary_analysis
      1
      0
      71
      0
      0.000000


      1
      eligible_primary_analysis
      1
      1
      11
      1
      0.090909


      2
      eligible_primary_analysis
      2
      0
      43
      6
      0.139535


      3
      eligible_primary_analysis
      2
      1
      6
      2
      0.333333


      4
      eligible_primary_analysis
      3
      0
      32
      2
      0.062500


      5
      eligible_primary_analysis
      3
      1
      15
      5
      0.333333


      6
      eligible_primary_analysis
      4
      0
      26
      8
      0.307692


      7
      eligible_primary_analysis
      4
      1
      25
      8
      0.320000















    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }



      const buttonEl =
        document.querySelector('#df-7b4f053f-0e93-4aae-9a46-d8ef1e5aa529 button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-7b4f053f-0e93-4aae-9a46-d8ef1e5aa529');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }

轻量统计检验：

    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }





      cohort_flag
      test
      statistic
      p_value




      0
      eligible_primary_analysis
      chi_square_phenotype_vs_hospital_mortality
      24.197919
      2.271254e-05


      1
      eligible_primary_analysis
      chi_square_phenotype_anemia_cells_vs_hospital_...
      32.745465
      2.952883e-05


      2
      eligible_primary_analysis
      kruskal_hb_min_48h_all_by_phenotype
      37.909810
      2.953512e-08


      3
      eligible_primary_analysis
      kruskal_gcs_motor_min_48h_by_phenotype
      171.490931
      6.064413e-37


      4
      eligible_primary_analysis
      kruskal_map_min_48h_by_phenotype
      78.676917
      5.899385e-17


      5
      eligible_primary_analysis
      kruskal_shock_index_max_48h_by_phenotype
      38.253358
      2.498054e-08


      6
      eligible_primary_analysis
      kruskal_lactate_max_48h_by_phenotype
      29.341537
      1.898267e-06


      7
      eligible_primary_analysis
      kruskal_spo2_fio2_min_48h_by_phenotype
      74.598476
      4.417340e-16


      8
      eligible_primary_analysis
      kruskal_creatinine_max_48h_by_phenotype
      35.467702
      9.703031e-08


      9
      eligible_primary_analysis
      kruskal_platelet_min_48h_by_phenotype
      25.325924
      1.319775e-05















    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }



      const buttonEl =
        document.querySelector('#df-a74564b2-9c38-4dcd-9f16-1a1b47bfa5ca button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-a74564b2-9c38-4dcd-9f16-1a1b47bfa5ca');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }

聚类稳定性：

    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }





      cohort_flag
      k
      comparison
      adjusted_rand_index




      0
      eligible_primary_analysis
      4
      kmeans_vs_hierarchical
      0.737865















    .colab-df-container {
      display:flex;
      gap: 12px;
    }

    .colab-df-convert {
      background-color: #E8F0FE;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      fill: #1967D2;
      height: 32px;
      padding: 0 0 0 0;
      width: 32px;
    }

    .colab-df-convert:hover {
      background-color: #E2EBFA;
      box-shadow: 0px 1px 2px rgba(60, 64, 67, 0.3), 0px 1px 3px 1px rgba(60, 64, 67, 0.15);
      fill: #174EA6;
    }

    .colab-df-buttons div {
      margin-bottom: 4px;
    }

    [theme=dark] .colab-df-convert {
      background-color: #3B4455;
      fill: #D2E3FC;
    }

    [theme=dark] .colab-df-convert:hover {
      background-color: #434B5C;
      box-shadow: 0px 1px 3px 1px rgba(0, 0, 0, 0.15);
      filter: drop-shadow(0px 1px 2px rgba(0, 0, 0, 0.3));
      fill: #FFFFFF;
    }



      const buttonEl =
        document.querySelector('#df-994141e0-dd81-4ac4-b084-d403c4e3a453 button.colab-df-convert');
      buttonEl.style.display =
        google.colab.kernel.accessAllowed ? 'block' : 'none';

      async function convertToInteractive(key) {
        const element = document.querySelector('#df-994141e0-dd81-4ac4-b084-d403c4e3a453');
        const dataTable =
          await google.colab.kernel.invokeFunction('convertToInteractive',
                                                    [key], {});
        if (!dataTable) return;

        const docLinkHtml = 'Like what you see? Visit the ' +
          '<a target="_blank" href=https://colab.research.google.com/notebooks/data_table.ipynb>data table notebook</a>'
          + ' to learn more about interactive tables.';
        element.innerHTML = '';
        dataTable['output_type'] = 'display_data';
        await google.colab.output.renderOutput(dataTable, element);
        const docLink = document.createElement('div');
        docLink.innerHTML = docLinkHtml;
        element.appendChild(docLink);
      }

写回 BigQuery：mimic-study-498508.ash_study.phenotype_cluster_centers_zscore (4 行)
写回 BigQuery：mimic-study-498508.ash_study.phenotype_cluster_assignments (229 行)
写回 BigQuery：mimic-study-498508.ash_study.phenotype_feature_summary_raw (4 行)
写回 BigQuery：mimic-study-498508.ash_study.phenotype_outcome_summary (4 行)
写回 BigQuery：mimic-study-498508.ash_study.phenotype_anemia_feasibility (8 行)
写回 BigQuery：mimic-study-498508.ash_study.phenotype_lightweight_tests (10 行)
写回 BigQuery：mimic-study-498508.ash_study.phenotype_cluster_stability (1 行)

分析完成。下一步请重点检查：

1. phenotype_k_selection_metrics：K=4 是否合理，是否存在过小 cluster
2. phenotype_cluster_centers_zscore：每类是否有清晰生理含义
3. phenotype_outcome_summary：不同 phenotype 死亡率是否有临床梯度
4. phenotype_anemia_feasibility：每个 phenotype x anemia 格子的死亡事件数是否足够
<Figure size 640x480 with 0 Axes>
