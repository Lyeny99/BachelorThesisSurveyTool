import os
import pickle
import pandas as pd
from loguru import logger


def save_session_state(session_data: dict, save_path: str):
    """
    Saves the current session state to a specified file path.

    Converts any DataFrames within `session_data` to dictionaries for serializability
    before saving, ensuring compatibility with the pickle format.

    Parameters:
        session_data (dict): Dictionary containing session data to be saved.
        save_path (str): File path where session data will be saved.
    """
    logger.info(f"Saving session state to {save_path}.")
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Convert DataFrames to dictionaries
        if isinstance(session_data.get("survey_file_1"), pd.DataFrame):
            session_data["survey_file_1"] = session_data["survey_file_1"].to_dict()
        if isinstance(session_data.get("survey_file_2"), pd.DataFrame):
            session_data["survey_file_2"] = session_data["survey_file_2"].to_dict()
        if isinstance(session_data.get("global_summary_table"), pd.DataFrame):
            session_data["global_summary_table"] = session_data[
                "global_summary_table"
            ].to_dict()

        # Save the global results
        if isinstance(session_data.get("global_results"), dict):
            session_data["global_results"] = session_data["global_results"]

        with open(save_path, "wb") as f:
            pickle.dump(session_data, f)
        logger.info(f"Session state saved successfully to {save_path}.")
    except Exception as e:
        logger.error(f"Failed to save session state: {e}", exc_info=True)


def load_session_state(session_path: str):
    """
    Loads session state from a specified file path.

    Converts dictionaries back to DataFrames for survey data if necessary.

    Parameters:
        session_path (str): File path from which session data will be loaded.

    Returns:
        dict: Loaded session data with DataFrames restored.

    Raises:
        FileNotFoundError: If the specified session file does not exist.
    """
    logger.info(f"Loading session state from {session_path}.")
    try:
        if not os.path.exists(session_path):
            logger.error(f"Session file not found: {session_path}.")
            raise FileNotFoundError("Session not found.")

        with open(session_path, "rb") as f:
            state = pickle.load(f)

        # Convert dictionaries back to DataFrames
        if isinstance(state.get("survey_file_1"), dict):
            state["survey_file_1"] = pd.DataFrame.from_dict(state["survey_file_1"])
        if isinstance(state.get("survey_file_2"), dict):
            state["survey_file_2"] = pd.DataFrame.from_dict(state["survey_file_2"])
        if isinstance(state.get("global_summary_table"), dict):
            state["global_summary_table"] = pd.DataFrame.from_dict(
                state["global_summary_table"]
            )

        logger.info(f"Session state loaded successfully from {session_path}.")
        return state
    except Exception as e:
        logger.error(f"Failed to load session state: {e}", exc_info=True)
        raise
