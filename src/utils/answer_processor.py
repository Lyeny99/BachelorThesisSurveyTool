import re
import pandas as pd
from loguru import logger


class AnswerProcessor:
    """
    Processes survey answers by standardizing binary responses, extracting numerical values
    from specific formats, and converting values to numeric types where applicable.
    """

    BINARY_MAPPING = {
        "Yes": 1,
        "No": 0,
        "True": 1,
        "False": 0,
        "Ja": 1,
        "Nein": 0,
        "Wahr": 1,
        "Falsch": 0,
    }

    @staticmethod
    def process_answer(answer: str):
        """
        Standardizes an individual answer by:
        - Converting binary responses to numeric (1 or 0) using BINARY_MAPPING.
        - Extracting and converting the number from "number - text" formats.
        - Attempting conversion to a float; returns the original text if not possible.

        Parameters:
            answer (str): The answer to process.

        Returns:
            int, float, or str: Processed answer in numeric form or original format if unchanged.
        """
        logger.debug(f"Processing answer: {answer}")
        # Standardize the answer to a string
        answer = str(answer).strip()

        # Convert binary answers to numeric
        if answer in AnswerProcessor.BINARY_MAPPING:
            mapped_value = AnswerProcessor.BINARY_MAPPING[answer]
            logger.debug(f"Mapped binary answer '{answer}' to {mapped_value}")
            return mapped_value

        # Check for "number - text" pattern and extract the number
        # for example in "1 - I am very satisfied" we are only interested in "1"
        # because it is a likert scale question
        # -> limesurvey just does not filter that before exporting data
        match = re.match(r"(-?\d+(?:\.\d+)?)\s*\-\s*.*", answer)
        if match:
            extracted_value = float(match.group(1))
            logger.debug(
                f"Extracted numeric value '{extracted_value}' from answer '{answer}'"
            )
            return extracted_value

        # Attempt to convert to float if possible
        try:
            converted_value = float(answer)
            logger.debug(
                f"Converted answer '{answer}' to numeric value {converted_value}"
            )
            return converted_value
        except ValueError:
            logger.debug(
                f"Answer '{answer}' could not be converted. Returning original value."
            )
            return answer

    @staticmethod
    def process_dataframe(df: pd.DataFrame):
        """
        Processes all answers in a DataFrame, applying `process_answer` to each
        column except the participant ID.

        Parameters:
            df (pd.DataFrame): DataFrame containing survey responses.

        Returns:
            pd.DataFrame: DataFrame with processed answers.
        """
        logger.info("Processing entire DataFrame.")
        processed_df = df.copy()
        for col in processed_df.columns[1:]:  # Skip participant ID
            logger.debug(f"Processing column: {col}")
            processed_df[col] = processed_df[col].apply(AnswerProcessor.process_answer)
        logger.info("DataFrame processing completed.")
        return processed_df
