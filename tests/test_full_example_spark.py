import os

from splink.spark.spark_linker import SparkLinker


from basic_settings import get_settings_dict


def test_full_example_spark(df_spark, tmp_path):
    settings_dict = get_settings_dict()

    # Overwrite the surname comparison to include duck-db specific syntax
    surname_match_level = {
        "sql_condition": "`surname_l` = `surname_r`",
        # "sql_condition": "surname_l similar to surname_r",
        "label_for_charts": "Exact match",
        "m_probability": 0.9,
        "u_probability": 0.1,
    }

    settings_dict["comparisons"][1]["comparison_levels"][1] = surname_match_level

    linker = SparkLinker(df_spark, settings_dict, break_lineage_method="checkpoint")

    linker.profile_columns(
        ["first_name", "surname", "first_name || surname", "concat(city, first_name)"]
    )
    linker.compute_tf_table("city")
    linker.compute_tf_table("first_name")

    linker.estimate_u_using_random_sampling(target_rows=1e6)

    blocking_rule = "l.first_name = r.first_name and l.surname = r.surname"
    linker.estimate_parameters_using_expectation_maximisation(blocking_rule)

    blocking_rule = "l.dob = r.dob"
    linker.estimate_parameters_using_expectation_maximisation(blocking_rule)

    df_predict = linker.predict()

    linker.comparison_viewer_dashboard(
        df_predict, os.path.join(tmp_path, "test_scv_spark.html"), True, 2
    )

    df_clusters = linker.cluster_pairwise_predictions_at_threshold(df_predict, 0.2)

    linker.cluster_studio_dashboard(
        df_predict,
        df_clusters,
        [0, 4],
        os.path.join(tmp_path, "test_cluster_studio.html"),
    )
