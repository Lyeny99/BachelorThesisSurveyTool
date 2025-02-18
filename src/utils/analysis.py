import pandas as pd
import numpy as np
from scipy.stats import shapiro, ttest_ind, wilcoxon
from loguru import logger

AVG = "avg"
SD = "sd"


class Analysis:
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
        logger.debug(f"Initialized Analysis with alpha={self.alpha}")

    def perform_hypothesis_testing(
        self, survey_1, survey_2, matched_pairs, test_method=None
    ):
        """
        Performs hypothesis testing using precomputed statistics.

        Parameters:
            survey_1: Survey 1 data object
            survey_2: Survey 2 data object
            matched_pairs: List of question pairs for comparison
            test_method: Specify the test method ('t-test', 'wilcoxon', or None for automatic selection)

        Returns:
            pd.DataFrame: DataFrame containing hypothesis testing results
        """
        logger.info("Starting hypothesis testing.")
        results = []
        for pair in matched_pairs:
            logger.debug(f"Processing question pair: {pair}")
            try:
                q1 = next(
                    q
                    for q in survey_1.questions
                    if q.question_text == pair["survey1_question"]
                )
                q2 = next(
                    q
                    for q in survey_2.questions
                    if q.question_text == pair["survey2_question"]
                )

                stats1 = survey_1.get_statistics(q1.question_id)
                stats2 = survey_2.get_statistics(q2.question_id)

                if not stats1 or not stats2:
                    logger.warning(f"Missing statistics for question pair: {pair}")
                    continue

                # acquire numeric answers for question
                data1 = survey_1.get_data_by_column(pair["survey1_question"])
                data2 = survey_2.get_data_by_column(pair["survey2_question"])

                data1 = pd.to_numeric(data1, errors="coerce").dropna()
                data2 = pd.to_numeric(data2, errors="coerce").dropna()

                if not self.is_numeric_or_binary(
                    data1
                ) or not self.is_numeric_or_binary(data2):
                    logger.warning(
                        f"Non-numeric or invalid data found for pair: {pair}. Skipping."
                    )
                    continue

                # [1] -> to only get p-value from results
                if test_method == "t-test":
                    test_type, p_value = (
                        "t-test",
                        ttest_ind(data1, data2, equal_var=True)[1],
                    )
                elif test_method == "wilcoxon":
                    min_len = min(
                        len(data1), len(data2)
                    )  # wilcoxon requires same length input
                    test_type, p_value = (
                        "Wilcoxon",
                        wilcoxon(data1.iloc[:min_len], data2.iloc[:min_len])[1],
                    )
                else:
                    p1, p2 = shapiro(data1)[1], shapiro(data2)[1]
                    if p1 > self.alpha and p2 > self.alpha:
                        test_type, p_value = (
                            "t-test",
                            ttest_ind(data1, data2, equal_var=True)[1],
                        )
                    else:
                        min_len = min(len(data1), len(data2))
                        test_type, p_value = (
                            "Wilcoxon",
                            wilcoxon(data1.iloc[:min_len], data2.iloc[:min_len])[1],
                        )

                results.append(
                    {
                        "Question": pair["unified_label"],
                        f"{survey_1.group} ({survey_1.survey_type}) AVG": round(
                            stats1[AVG], 2
                        ),
                        f"{survey_1.group} ({survey_1.survey_type}) SD": round(
                            stats1[SD], 2
                        ),
                        f"{survey_2.group} ({survey_2.survey_type}) AVG": round(
                            stats2[AVG], 2
                        ),
                        f"{survey_2.group} ({survey_2.survey_type}) SD": round(
                            stats2[SD], 2
                        ),
                        "p-value": round(p_value, 3),
                        "Test Used": test_type,
                    }
                )
                logger.debug(f"Test result for pair {pair}: {results[-1]}")

            except Exception as e:
                logger.error(f"Error processing pair {pair}: {e}", exc_info=True)

        logger.info("Hypothesis testing completed.")
        return pd.DataFrame(results)

    def is_numeric_or_binary(self, data):
        """
        Checks if the provided data is numeric or binary.

        Parameters:
            data (np.array or pd.Series): Data to check.

        Returns:
            bool: True if numeric or binary, False otherwise.
        """
        unique_values = np.unique(data)
        is_valid = len(unique_values) == 2 or np.issubdtype(data.dtype, np.number)
        logger.debug(f"Data validity check: {is_valid}")
        return is_valid
