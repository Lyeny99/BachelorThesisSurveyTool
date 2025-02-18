import os
import pandas as pd
import matplotlib.pyplot as plt
from loguru import logger
from typing import List

from src.models.survey import Survey
from src.models.question import Question


class ChartBuilder:
    """
    Generates and manages charts for comparing survey data.

    Attributes:
        survey1 (Survey): Data for the first survey.
        survey2 (Survey): Data for the second survey.
        charts_folder (str): Directory to save generated charts.
        label_history (dict): Maps shortened labels to full question text.
        bar_colors (list): Colors for bar charts.
        text_color (str): Color for chart text.
        background_color (str): Color for chart background.
    """

    def __init__(
        self, survey1: Survey, survey2: Survey, charts_folder: str, color_scheme=None
    ):
        logger.info("Initializing ChartBuilder.")
        self.survey1 = survey1
        self.survey2 = survey2
        self.charts_folder = charts_folder
        self.label_history = {}

        os.makedirs(self.charts_folder, exist_ok=True)
        logger.debug(f"Charts folder set to: {self.charts_folder}")

        # Set color scheme with defaults if none provided
        default_colors = ["#1982c4", "#8ac926"]
        self.bar_colors = (
            [
                color_scheme.colors.get("color3", default_colors[0]),
                color_scheme.colors.get("color4", default_colors[1]),
            ]
            if color_scheme
            else default_colors
        )
        self.text_color = "#000000"
        self.background_color = "#ffffff"
        logger.debug(f"Bar colors: {self.bar_colors}")

    def _set_chart_properties(self, title: str, xlabel: str, ylabel: str):
        """Applies consistent title, label, and tick styling for charts."""
        logger.debug(f"Setting chart properties: title={title}")
        plt.title(title, fontsize=16, color=self.text_color)
        plt.xlabel(xlabel, fontsize=12, color=self.text_color)
        plt.ylabel(ylabel, fontsize=12, color=self.text_color)
        plt.xticks(rotation=45, ha="right", color=self.text_color)
        plt.gca().set_facecolor(self.background_color)
        plt.gcf().set_facecolor(self.background_color)

    def _plot_bar_chart(
        self, data: pd.DataFrame, title: str, xlabel: str, ylabel: str, filename: str
    ):
        """Plots a bar chart and saves it to file."""
        logger.debug(f"Plotting bar chart: {filename}")
        data.plot(kind="bar", color=self.bar_colors, figsize=(12, 6))
        self._set_chart_properties(title, xlabel, ylabel)
        self._save_chart(filename)

    def _shorten_label(self, label: str, max_length=10):
        """Shortens a label if it exceeds max_length and records it in label_history."""
        if len(label) > max_length:
            short_label = f"Q{len(self.label_history) + 1}"
            self.label_history[short_label] = label
            logger.debug(f"Shortened label '{label}' to '{short_label}'")
            return short_label
        return label

    def _save_chart(self, filename: str):
        """Saves the current chart and its labels."""
        filepath = self.charts_folder + f"/{filename}.jpg"
        plt.tight_layout()  # Adjust layout to prevent clipping
        plt.savefig(filepath, format="jpg")
        plt.close()
        logger.info(f"Chart saved: {filepath}")
        self._save_labels_to_csv(filename)

    def _save_labels_to_csv(self, filename: str):
        """Saves label history to a CSV file."""
        if self.label_history:
            csv_filepath = self.charts_folder + f"{filename}_labels.csv"
            pd.DataFrame(
                self.label_history.items(), columns=["Short Label", "Full Label"]
            ).to_csv(csv_filepath, index=False)
            logger.info(f"Labels saved to CSV: {csv_filepath}")

    def generate_charts(self, summary_table: pd.DataFrame, keywords: List[str] = None):
        """
        Generates charts based on question types and summary statistics.

        Parameters:
            summary_table (pd.DataFrame): Summary statistics for matched questions.
            keywords (list of str): Keywords for selecting related questions.
        """
        logger.info("Generating charts.")
        self.clear_existing_charts()

        numerical_questions = self._select_numerical_questions()
        binary_questions = self._select_binary_questions()
        significant_questions = self._select_significant_questions(summary_table)
        related_questions = self._select_related_questions(keywords)

        if numerical_questions:
            self._plot_aggregate_comparison(numerical_questions, measure="average")

        if binary_questions:
            self._plot_aggregate_comparison(binary_questions, measure="proportion")

        for question in significant_questions:
            self._plot_significant_question_comparison(question)

        if related_questions:
            self._plot_combined_related_questions(related_questions)

    def _plot_aggregate_comparison(
        self, questions: List[Question], measure: str = "average"
    ):
        """Plots aggregate comparison for numerical or binary questions."""
        logger.debug(f"Plotting aggregate comparison: measure={measure}")
        values_survey1 = [
            (
                self.survey1.get_data_by_question_id(q.question_id).mean()
                if measure == "average"
                else self.survey1.get_data_by_question_id(q.question_id)
                .value_counts(normalize=True)
                .get(1, 0)
            )
            for q in questions
        ]
        values_survey2 = [
            (
                self.survey2.get_data_by_question_id(q.question_id).mean()
                if measure == "average"
                else self.survey2.get_data_by_question_id(q.question_id)
                .value_counts(normalize=True)
                .get(1, 0)
            )
            for q in questions
        ]

        shortened_labels = [self._shorten_label(q.question_text) for q in questions]
        combined_df = pd.DataFrame(
            {
                f"Survey {self.survey1.survey_id}": values_survey1,
                f"Survey {self.survey2.survey_id}": values_survey2,
            },
            index=shortened_labels,
        )

        title = (
            "Average Responses for Numerical Questions"
            if measure == "average"
            else "Proportion of Positive Responses for Binary Questions"
        )
        ylabel = (
            "Average Response"
            if measure == "average"
            else "Proportion of Positive Responses"
        )
        filename = (
            "aggregate_numerical_comparison"
            if measure == "average"
            else "aggregate_binary_comparison"
        )

        self._plot_bar_chart(combined_df, title, "Questions", ylabel, filename)

    def _plot_significant_question_comparison(self, question: Question):
        """Plots a chart for questions with significant differences."""
        logger.debug(
            f"Plotting significant question comparison for: {question.question_text}"
        )
        data1 = self.survey1.get_data_by_question_id(question.question_id)
        data2 = self.survey2.get_data_by_question_id(question.question_id)

        combined_df = pd.DataFrame(
            {
                f"Survey {self.survey1.survey_id}": data1.value_counts(normalize=True),
                f"Survey {self.survey2.survey_id}": data2.value_counts(normalize=True),
            }
        ).fillna(0)

        short_label = self._shorten_label(question.question_text)
        self._plot_bar_chart(
            combined_df,
            f'Significant Difference for "{short_label}"',
            "Responses",
            "Proportion of Participants",
            f"significant_question_{short_label}",
        )

    def _plot_combined_related_questions(self, questions):
        """Plots a combined chart for related questions."""
        logger.debug("Plotting combined related questions.")
        avg_survey1 = [
            self.survey1.get_data_by_question_id(q.question_id).mean()
            for q in questions
        ]
        avg_survey2 = [
            self.survey2.get_data_by_question_id(q.question_id).mean()
            for q in questions
        ]
        shortened_labels = [self._shorten_label(q.question_text) for q in questions]

        combined_df = pd.DataFrame(
            {
                f"Survey {self.survey1.survey_id}": avg_survey1,
                f"Survey {self.survey2.survey_id}": avg_survey2,
            },
            index=shortened_labels,
        )

        self._plot_bar_chart(
            combined_df,
            "Combined Responses for Questions with Keywords",
            "Questions",
            "Average Response",
            "combined_related_questions",
        )

    def clear_existing_charts(self):
        """Deletes all existing charts in the folder."""
        logger.info("Clearing existing charts.")
        if os.path.exists(self.charts_folder):
            for file in os.listdir(self.charts_folder):
                if file.endswith(".jpg") or file.endswith(".csv"):
                    os.remove(self.charts_folder + file)
            logger.info("Existing charts cleared.")

    def _select_numerical_questions(self):
        """Selects numerical questions for plotting."""
        numerical_questions = [
            q for q in self.survey1.questions if q.answer_type == "num"
        ]
        logger.debug(f"Numerical questions selected: {len(numerical_questions)}")
        return numerical_questions

    def _select_binary_questions(self):
        """Selects binary questions for plotting."""
        binary_questions = [
            q for q in self.survey1.questions if q.answer_type == "binary"
        ]
        logger.debug(f"Binary questions selected: {len(binary_questions)}")
        return binary_questions

    def _select_significant_questions(
        self, summary_table: pd.DataFrame, alpha: float = 0.05
    ):
        """Selects significant questions based on p-values."""
        logger.debug("Selecting significant questions.")
        if "Question" in summary_table.columns:
            summary_table = summary_table.set_index("Question")

        significant_questions = [
            q
            for q in self.survey1.questions
            if q.question_text in summary_table.index
            and summary_table.loc[q.question_text]["p-value"] < alpha
        ]
        logger.debug(f"Significant questions selected: {len(significant_questions)}")
        return significant_questions

    def _select_related_questions(self, keywords: List[str]):
        """Selects questions related to specific keywords."""
        logger.debug(f"Selecting related questions using keywords: {keywords}")
        keywords = [k.lower() for k in keywords]
        related_questions = [
            q
            for q in self.survey1.questions
            if any(keyword in q.question_text.lower() for keyword in keywords)
        ]
        logger.debug(f"Related questions selected: {len(related_questions)}")
        return related_questions
