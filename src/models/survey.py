import dataclasses
from typing import List
import pandas as pd
from loguru import logger
from src.models.question import Question
from src.models.result import Result, Answer
from src.utils.answer_processor import AnswerProcessor
from src.utils.data_preparer import QuestionMatcher

AVG = "avg"
SD = "sd"


@dataclasses.dataclass
class Survey:
    """
    Represents a survey with metadata, questions, results, and a DataFrame of responses.

    Attributes:
        survey_id (int): Unique identifier for the survey.
        group (str): Survey group designation (e.g., A or B).
        survey_type (str): Type of survey (e.g., pre or post).
        questions (list[Question]): List of survey questions.
        results (list[Result]): List of survey results.
        dataframe (pd.DataFrame): DataFrame containing survey responses.
    """

    survey_id: int
    group: str
    survey_type: str  # pre/post
    questions: list[Question]
    results: list[Result]
    dataframe: pd.DataFrame = None
    statistics: dict = None

    def update_metadata(self, survey_id: int, group: str, survey_type: str):
        """Updates the survey's ID, group, and type if provided values are non-default."""
        logger.debug(
            f"Updating metadata: survey_id={survey_id}, group={group}, survey_type={survey_type}"
        )
        if survey_id != 0:
            self.survey_id = survey_id
        if group != "":
            self.group = group
        if survey_type != "":
            self.survey_type = survey_type

    def add_question(self, question_text: str, answer_type: str, raw_text: str) -> int:
        """Adds a question to the survey and returns the new question ID."""
        question_id = len(self.questions) + 1
        question = Question(question_id, question_text, answer_type, raw_text=raw_text)
        self.questions.append(question)
        logger.debug(f"Added question: {question}")
        return question_id

    def add_result(self, participant_id: int, answers: List[Answer]):
        """Adds a participant's result (with answers) to the survey."""
        result = Result(participant_id, self.survey_id, answers)
        self.results.append(result)
        logger.debug(f"Added result for participant_id={participant_id}")

    def set_dataframe(self, df: pd.DataFrame):
        """Sets the survey's response data as a DataFrame."""
        self.dataframe = df
        logger.debug("DataFrame set for survey.")

    def get_column_names(self):
        """Returns column names from the DataFrame, excluding participant ID."""
        if self.dataframe is not None:
            return self.dataframe.columns[1:]  # Skip the first column (participant ID)
        return []

    def get_data_by_column(self, question_text: str):
        """
        Retrieves and cleans numeric data for a specific question based on its cleaned text.

        Parameters:
            question_text (str): The cleaned text of the question.

        Returns:
            pd.Series: The numeric data for the question, or an empty Series if no valid data is found.
        """
        logger.debug(f"Getting data for column: {question_text}")
        question = next(
            (q for q in self.questions if q.question_text == question_text), None
        )
        if not question:
            logger.warning(f"Question '{question_text}' not found in the survey.")
            return pd.Series(dtype=float)

        question_id = question.question_id
        # goes through all answers of all results
        # gets answers with right question id and numeric
        # converts to float
        answers = [
            float(answer.answer)
            for result in self.results
            for answer in result.answers
            if answer.question_id == question_id
            and isinstance(answer.answer, (int, float))
        ]

        if answers:
            return pd.Series(answers, dtype=float)
        else:
            logger.warning(f"No numeric answers found for question '{question_text}'.")
            return pd.Series(dtype=float)

    def get_question_text_by_id(self):
        """Returns a dictionary mapping question IDs to question text."""
        return {q.question_id: q.question_text for q in self.questions}

    def get_data_by_question_id(self, question_id: int):
        """
        Retrieves and cleans numeric data for a specific question based on its question_id.

        Parameters:
            question_id (int): The ID of the question.

        Returns:
            pd.Series: The numeric data for the question, or an empty Series if no valid data is found.
        """
        logger.debug(f"Getting data for question_id: {question_id}")
        answers = [
            float(answer.answer)
            for result in self.results
            for answer in result.answers
            if answer.question_id == question_id
            and isinstance(answer.answer, (int, float))
        ]

        if answers:
            return pd.Series(answers, dtype=float)
        else:
            logger.warning(f"No data found for question_id={question_id}")
            return pd.Series(dtype=float)

    def add_statistics(self, question_id, avg, sd):
        """Stores average and standard deviation for a specific question."""
        logger.debug(
            f"Adding statistics for question_id={question_id}: {AVG}={avg}, {SD}={sd}"
        )
        if self.statistics is None:
            self.statistics = {}
        self.statistics[question_id] = {AVG: avg, SD: sd}

    def get_statistics(self, question_id):
        """Retrieves precomputed statistics for a question, if available."""
        stats = self.statistics.get(question_id) if self.statistics else None
        logger.debug(f"Statistics for question_id={question_id}: {stats}")
        return stats

    def clear_statistics(self):
        """Clears all stored statistics."""
        logger.debug("Clearing all statistics.")
        self.statistics = {}

    def populate_data(self):
        """
        Populates questions and results into the Survey object.
        Converts answers to numeric and binary formats where applicable for analysis purposes.
        Ensures that `answer_type` is determined from the cleaned answers.
        """
        logger.info("Populating survey data.")
        question_matcher = QuestionMatcher()

        processed_df = AnswerProcessor.process_dataframe(self.dataframe)
        logger.debug("Processed DataFrame for answers.")

        for idx, raw_column_name in enumerate(
            self.dataframe.columns[1:]
        ):  # Skip participant ID
            cleaned_question = question_matcher.clean_text(raw_column_name)
            cleaned_answers = processed_df.iloc[:, idx + 1]
            answer_type = self.determine_answer_type(cleaned_answers)
            self.add_question(cleaned_question, answer_type, raw_column_name)

        for _, row in processed_df.iterrows():
            answers = [
                Answer(question_id=idx + 1, answer=row[col])
                for idx, col in enumerate(processed_df.columns[1:])
            ]
            self.add_result(participant_id=row.iloc[0], answers=answers)

        logger.info("Survey data population completed.")

    @staticmethod
    def determine_answer_type(column: pd.Series):
        """
        Determines the answer type for a given column.
        - Returns "num" for numeric data.
        - Returns "binary" for columns with two unique values.
        - Returns "text" for all other data types.
        """
        if pd.api.types.is_numeric_dtype(column):
            return "num"
        elif len(column.dropna().unique()) == 2:
            return "binary"
        else:
            return "text"
