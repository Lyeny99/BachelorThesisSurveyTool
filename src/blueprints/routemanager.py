import os
import zipfile
import io
from typing import List
from datetime import datetime
from io import StringIO
from loguru import logger

from flask import Blueprint, request, render_template, send_file

import pandas as pd

from src.models.survey import Survey
from src.models.color_scheme import ColorScheme
from src.models.keywords import KeywordManager
from src.utils.chart_builder import ChartBuilder
from src.utils.session_manager import save_session_state, load_session_state
from src.utils.analysis import Analysis
from src.utils.data_preparer import DataPreparer

routemanager = Blueprint("routemanager", __name__, template_folder="templates")

DEFAULT_ALPHA = 0.5
alpha = DEFAULT_ALPHA
DEFAULT_TEST_METHOD = "automatic"
test_method = DEFAULT_TEST_METHOD


survey_1_in_memory = Survey(
    survey_id=0,
    group="",
    survey_type="post",
    questions=[],
    results=[],
    dataframe=pd.DataFrame(),
)
survey_2_in_memory = Survey(
    survey_id=0,
    group="",
    survey_type="post",
    questions=[],
    results=[],
    dataframe=pd.DataFrame(),
)

global_results = pd.DataFrame()
global_summary_table = None
isNormalized = "EMPTY"

current_session_name = ""
image_path = os.getcwd() + "/static/images/"
sessions_path = os.getcwd() + "/static/sessions/"

available_themes = ColorScheme.load_schemes()
selected_theme = next(
    (theme for theme in available_themes if theme.name == "default"),
    available_themes[0] if available_themes else None,
)

# -----------------------------------------------------------------------------------------
# General
@routemanager.route("/")
def general():
    logger.info("Entered general function.")
    logger.info("Rendering general page.")
    return render_template("general.html")


# -----------------------------------------------------------------------------------------
# Survey
@routemanager.route("/survey")
def survey():
    logger.info("Entered survey function.")
    logger.info("Rendering survey page.")
    file1_id = request.form.get("file1_id", "1")
    file1_type = request.form.get("file1_type", "post")
    file1_group = request.form.get("file1_group", "A")

    file2_id = request.form.get("file2_id", "2")
    file2_type = request.form.get("file2_type", "post")
    file2_group = request.form.get("file2_group", "B")

    logger.debug(
        f"Survey parameters - file1: {file1_id}, {file1_type}, {file1_group}; file2: {file2_id}, {file2_type}, {file2_group}"
    )
    return render_template(
        "survey.html",
        file1_id=file1_id,
        file1_type=file1_type,
        file1_group=file1_group,
        file2_id=file2_id,
        file2_type=file2_type,
        file2_group=file2_group,
    )


# -----------------------------------------------------------------------------------------
@routemanager.route("/loadsurveyfromfile", methods=["POST"])
def loadsurveyfromfile():
    logger.info("Entered loadsurveyfromfile function.")
    try:
        logger.info("Started loading surveys from files.")
        global current_session_name, alpha, test_method, survey_1_in_memory, survey_2_in_memory

        if "file1" not in request.files or "file2" not in request.files:
            logger.warning("Both survey files must be uploaded.")
            raise ValueError("Both survey files must be uploaded.")

        file1_id = request.form.get("file1_id", "1")
        file1_type = request.form.get("file1_type", "post")
        file1_group = request.form.get("file1_group", "A")
        file1 = request.files["file1"]

        file2_id = request.form.get("file2_id", "2")
        file2_type = request.form.get("file2_type", "post")
        file2_group = request.form.get("file2_group", "B")
        file2 = request.files["file2"]

        logger.debug(f"File details - file1: {file1.filename}, file2: {file2.filename}")

        if file1.filename == "" or file2.filename == "":
            logger.warning("Files must have valid names.")
            raise ValueError("Files must have valid names.")

        # Load Survey 1
        if file1 and file1.filename.endswith(".csv"):
            logger.info("Processing Survey 1 file.")
            file_content = StringIO(file1.stream.read().decode("utf-8"))
            df1 = pd.read_csv(file_content)
            if df1.empty:
                logger.warning("Survey 1 file is empty.")
                raise ValueError("Survey 1 file is empty.")
            survey_1_in_memory = Survey(
                survey_id=int(file1_id),
                group=file1_group,
                survey_type=file1_type,
                dataframe=df1,
                questions=[],
                results=[],
            )
            survey_1_in_memory.populate_data()
        else:
            logger.warning("Invalid file format for Survey 1.")
            raise ValueError(
                "Invalid file format for Survey 1. Only .csv files are supported."
            )

        # Load Survey 2
        if file2 and file2.filename.endswith(".csv"):
            logger.info("Processing Survey 2 file.")
            file_content = StringIO(file2.stream.read().decode("utf-8"))
            df2 = pd.read_csv(file_content)
            if df2.empty:
                logger.warning("Survey 2 file is empty.")
                raise ValueError("Survey 2 file is empty.")
            survey_2_in_memory = Survey(
                survey_id=int(file2_id),
                group=file2_group,
                survey_type=file2_type,
                dataframe=df2,
                questions=[],
                results=[],
            )
            survey_2_in_memory.populate_data()
        else:
            logger.warning("Invalid file format for Survey 2.")
            raise ValueError(
                "Invalid file format for Survey 2. Only .csv files are supported."
            )

        if survey_1_in_memory.dataframe.empty or survey_2_in_memory.dataframe.empty:
            logger.error("Both surveys must contain valid data.")
            raise ValueError("Both surveys must contain valid data.")

        new_session_flag = True
        if current_session_name:
            try:
                _, session_ids = current_session_name.split("_")
                session_file1_id, session_file2_id = session_ids.split("-")
                session_file2_id = session_file2_id.split(".")[0]

                if session_file1_id == file1_id and session_file2_id == file2_id:
                    error_message, status = perform_analysis()
                    update_session()
                    if status == "error":
                        logger.warning("Error occurred during analysis.")
                        return render_template(
                            "survey.html",
                            error_message=error_message,
                            file1_id=file1_id,
                            file1_type=file1_type,
                            file1_group=file1_group,
                            file2_id=file2_id,
                            file2_type=file2_type,
                            file2_group=file2_group,
                        )
                    else:
                        new_session_flag = False
            except ValueError:
                current_session_name = None

        if new_session_flag:
            alpha = DEFAULT_ALPHA
            test_method = DEFAULT_TEST_METHOD
            current_date = datetime.now().strftime("%d-%m-%Y")
            current_session_name = f"{current_date}_{file1_id}-{file2_id}.pkl"

            error_message, status = perform_analysis()
            save_session()
            if status == "error":
                logger.warning("Error during new session analysis.")
                return render_template(
                    "survey.html",
                    error_message=error_message,
                    file1_id=file1_id,
                    file1_type=file1_type,
                    file1_group=file1_group,
                    file2_id=file2_id,
                    file2_type=file2_type,
                    file2_group=file2_group,
                )

        logger.info("Surveys loaded and session updated successfully.")
        return render_template(
            "survey.html",
            message="Surveys loaded successfully.",
            file1_id=file1_id,
            file1_type=file1_type,
            file1_group=file1_group,
            file2_id=file2_id,
            file2_type=file2_type,
            file2_group=file2_group,
        )

    except ValueError as e:
        logger.warning(f"Input Error: {e}")
        return render_template(
            "survey.html",
            error_message=f"Input Error: {str(e)}",
            file1_id=request.form.get("file1_id", "1"),
            file1_type=request.form.get("file1_type", "post"),
            file1_group=request.form.get("file1_group", "A"),
            file2_id=request.form.get("file2_id", "2"),
            file2_type=request.form.get("file2_type", "post"),
            file2_group=request.form.get("file2_group", "B"),
        )
    except pd.errors.ParserError:
        logger.error("Failed to parse CSV files.", exc_info=True)
        return render_template(
            "survey.html",
            error_message="Failed to parse CSV files. Check file format.",
            file1_id=request.form.get("file1_id", "1"),
            file1_type=request.form.get("file1_type", "post"),
            file1_group=request.form.get("file1_group", "A"),
            file2_id=request.form.get("file2_id", "2"),
            file2_type=request.form.get("file2_type", "post"),
            file2_group=request.form.get("file2_group", "B"),
        )
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return render_template(
            "survey.html",
            error_message=f"An unexpected error occurred: {str(e)}",
            file1_id=request.form.get("file1_id", "1"),
            file1_type=request.form.get("file1_type", "post"),
            file1_group=request.form.get("file1_group", "A"),
            file2_id=request.form.get("file2_id", "2"),
            file2_type=request.form.get("file2_type", "post"),
            file2_group=request.form.get("file2_group", "B"),
        )


# -----------------------------------------------------------------------------------------
def perform_analysis():
    logger.info("Entered perform_analysis function.")
    try:
        global global_results, global_summary_table, isNormalized

        if survey_1_in_memory.dataframe.empty or survey_2_in_memory.dataframe.empty:
            logger.error("No survey data available for analysis.")
            raise ValueError("No survey data available.")

        # Step 1: Prepare data
        logger.info("Preparing data for analysis.")
        data_preparer = DataPreparer()
        matched_pairs = data_preparer.prepare_surveys(
            survey_1_in_memory, survey_2_in_memory
        )

        # Step 2: Perform hypothesis testing
        logger.info("Performing hypothesis testing.")
        analyser = Analysis(alpha=alpha)
        hypothesis_results, isNormalized = analyser.perform_hypothesis_testing(
            survey_1_in_memory, survey_2_in_memory, matched_pairs, test_method
        )

        # Free up memory by clearing statistics after completing analysis.
        logger.info("Clearing statistics to free up memory.")
        survey_1_in_memory.clear_statistics()
        survey_2_in_memory.clear_statistics()

        # Store results globally
        logger.info("Storing analysis results globally.")
        global_summary_table = hypothesis_results
        global_results = hypothesis_results.set_index("Question").T.to_dict()

        # Step 4: Generate charts
        logger.info("Generating charts.")
        charts_folder = image_path + os.path.splitext(current_session_name)[0] + "/"
        chart_builder = ChartBuilder(
            survey_1_in_memory,
            survey_2_in_memory,
            charts_folder,
            color_scheme=selected_theme,
        )

        # Load user-defined keywords
        user_keywords = KeywordManager.load_keywords()
        logger.debug(f"Using keywords for chart generation: {user_keywords}")

        chart_builder.generate_charts(hypothesis_results, keywords=user_keywords)

        logger.info("Analysis completed successfully.")
        return "Analysis completed successfully.", "success"

    except ValueError as e:
        logger.warning(f"Value Error occurred during analysis: {e}")
        return f"Value Error occurred during analysis: {str(e)}", "error"
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during analysis: {e}", exc_info=True
        )
        return f"An unexpected error occurred during analysis: {str(e)}", "error"


# -----------------------------------------------------------------------------------------
# Analysis
@routemanager.route("/analysis", methods=["GET", "POST"])
def analysis():
    logger.info("Entered analysis function.")
    if request.method == "POST":
        logger.info("Received POST request for analysis.")
        global alpha, test_method
        alpha = float(request.form["alpha"])
        test_method = request.form.get("test-method", "automatic")

        logger.debug(f"Alpha: {alpha}, Test Method: {test_method}")
        message, status = perform_analysis()

        logger.info("Rendering analysis page with results.")
        return render_template(
            "analysis.html",
            results=global_results,
            survey1=survey_1_in_memory,
            survey2=survey_2_in_memory,
            alpha=alpha,
            test_method=test_method,
            message=message,
            status=status,
            isNormalized=isNormalized
        )

    logger.info("Rendering analysis page without recalculation.")
    return render_template(
        "analysis.html",
        results=global_results,
        survey1=survey_1_in_memory,
        survey2=survey_2_in_memory,
        alpha=alpha,
        test_method=test_method,
        isNormalized=isNormalized
    )


# -----------------------------------------------------------------------------------------
@routemanager.route("/export_data", methods=["POST"])
def export_data():
    logger.info("Entered export_data function.")
    try:
        latex_filename = request.form.get("latex_filename", "analysis_results.tex")
        csv_filename = request.form.get("csv_filename", "dataframe_export.csv")
        export_type = request.form.get("export_type")

        logger.debug(
            f"Export parameters - Latex Filename: {latex_filename}, CSV Filename: {csv_filename}, Export Type: {export_type}"
        )

        latex_filepath = "/tmp/" + latex_filename
        csv_filepath = "/tmp/" + csv_filename

        if export_type == "latex":
            logger.info("Exporting data as LaTeX.")
            latex_table = global_summary_table.to_latex(
                index=False, header=True, caption="Survey Analysis Results"
            )

            with open(latex_filepath, "w", encoding="utf-8") as f:
                f.write(latex_table)
            logger.info("LaTeX file created successfully.")
            return send_file(latex_filepath, as_attachment=True)

        elif export_type == "csv":
            logger.info("Exporting data as CSV.")
            global_summary_table.to_csv(csv_filepath, index=False)
            logger.info("CSV file created successfully.")
            return send_file(csv_filepath, as_attachment=True)

        logger.warning("Invalid file type specified for export.")
        raise ValueError("Invalid filetype for export")

    except ValueError as e:
        logger.warning(f"Value Error during data export: {e}")
        return render_template(
            "error.html", error_message=f"Failed to export data: {str(e)}"
        )
    except FileNotFoundError:
        logger.error("File not found during export.")
        return render_template("error.html", error_message="File not found.")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during data export: {e}", exc_info=True
        )
        return render_template(
            "error.html", error_message=f"Failed to export data:{str(e)}"
        )


# -----------------------------------------------------------------------------------------
# Data
@routemanager.route("/data")
def data():
    logger.info("Entered data function.")
    try:
        logger.info("Fetching survey question maps.")
        survey1_questions_map = survey_1_in_memory.get_question_text_by_id()
        survey2_questions_map = survey_2_in_memory.get_question_text_by_id()

        logger.info("Rendering data page.")
        return render_template(
            "data.html",
            survey1=survey_1_in_memory,
            survey2=survey_2_in_memory,
            survey1_questions_map=survey1_questions_map,
            survey2_questions_map=survey2_questions_map,
        )
    except Exception as e:
        logger.error(
            f"An unexpected error occurred in data function: {e}", exc_info=True
        )
        return render_template(
            "error.html", error_message=f"Failed to load data page: {str(e)}"
        )


# -----------------------------------------------------------------------------------------
# Graphs
@routemanager.route("/graphs")
def graphs():
    logger.info("Entered graphs function.")
    try:
        logger.info("Fetching chart files.")
        charts_folder = image_path + os.path.splitext(current_session_name)[0] + "/"

        if os.path.exists(charts_folder):
            chart_files = [
                f"images/{os.path.splitext(current_session_name)[0]}/{f}"
                for f in os.listdir(charts_folder)
                if f.endswith(".jpg") or f.endswith(".png")
            ]
            logger.debug(f"Found chart files: {chart_files}")
        else:
            logger.warning("Charts folder does not exist.")
            chart_files = []

        logger.info("Rendering graphs page.")
        return render_template("graphs.html", chart_files=chart_files)

    except Exception as e:
        logger.error(
            f"An unexpected error occurred in graphs function: {e}", exc_info=True
        )
        return render_template(
            "error.html", error_message=f"Failed to load charts: {str(e)}"
        )


# -----------------------------------------------------------------------------------------
@routemanager.route("/export/<filename>")
def export_graph(filename: str):
    logger.info(f"Entered export_graph function for filename: {filename}")
    try:
        charts_folder = image_path + os.path.splitext(current_session_name)[0] + "/"
        image_file_path = charts_folder + filename
        label_file_path = charts_folder + filename.split(".")[0] + "_labels.csv"

        if not os.path.exists(image_file_path):
            logger.error(f"File {filename} not found in the current session.")
            raise FileNotFoundError(
                f"File {filename} not found in the current session."
            )

        logger.info(f"Preparing files for export: {filename}")
        file_paths = [(image_file_path, filename)]

        if os.path.exists(label_file_path):
            file_paths.append((label_file_path, f"{filename.split('.')[0]}_labels.csv"))

        zip_buffer = create_zip(file_paths)
        logger.info("ZIP file created successfully.")
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f"{filename.split('.')[0]}.zip",
            mimetype="application/zip",
        )

    except FileNotFoundError as e:
        logger.warning(f"FileNotFoundError: {e}")
        return render_template("error.html", error_message=str(e))
    except PermissionError:
        logger.warning("Permission denied when accessing the file.")
        return render_template(
            "error.html", error_message="Permission denied when accessing the file."
        )
    except Exception as e:
        logger.error(f"Unexpected error in export_graph: {e}", exc_info=True)
        return render_template(
            "error.html", error_message=f"Unexpected error: {str(e)}"
        )


# -----------------------------------------------------------------------------------------
@routemanager.route("/export_all_graphs")
def export_all_graphs():
    logger.info("Entered export_all_graphs function.")
    try:
        charts_folder = image_path + os.path.splitext(current_session_name)[0] + "/"

        file_paths = []
        for filename in os.listdir(charts_folder):
            if filename.endswith(".jpg"):
                img_path = charts_folder + filename
                file_paths.append((img_path, filename))

                label_filename = f"{filename.split('.')[0]}_labels.csv"
                label_path = charts_folder + label_filename
                if os.path.exists(label_path):
                    file_paths.append((label_path, label_filename))

        zip_buffer = create_zip(file_paths)
        logger.info("All graphs exported successfully.")
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name="all_charts.zip",
            mimetype="application/zip",
        )
    except Exception as e:
        logger.error(f"Failed to export all graphs: {e}", exc_info=True)
        return render_template(
            "error.html", error_message=f"Failed to export all graphs: {str(e)}"
        )


# -----------------------------------------------------------------------------------------
def create_zip(file_paths: List):
    logger.info("Creating ZIP file.")
    zip_buffer = io.BytesIO()
    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, arcname in file_paths:
                if os.path.exists(file_path):
                    logger.debug(f"Adding {arcname} to ZIP.")
                    zip_file.write(file_path, arcname=arcname)
    except Exception as e:
        logger.error(f"Error while creating ZIP: {e}", exc_info=True)
        raise
    zip_buffer.seek(0)
    logger.info("ZIP file created successfully.")
    return zip_buffer


# -----------------------------------------------------------------------------------------
def generate_charts_based_on_analysis():
    logger.info("Generating charts based on analysis.")
    charts_folder = image_path + os.path.splitext(current_session_name)[0] + "/"

    if os.path.exists(charts_folder):
        logger.info("Clearing existing images in the charts folder.")
        for file_name in os.listdir(charts_folder):
            file_path = charts_folder + file_name
            if (
                file_name.endswith(".jpg")
                or file_name.endswith(".png")
                or file_name.endswith(".csv")
            ):
                os.remove(file_path)

    theme_colors = selected_theme or next(
        (theme for theme in available_themes if theme.name == "default"), None
    )

    chart_builder = ChartBuilder(
        survey_1_in_memory, survey_2_in_memory, charts_folder, color_scheme=theme_colors
    )

    # Load user-defined keywords
    user_keywords = KeywordManager.load_keywords()
    logger.debug(f"Using keywords for chart generation: {user_keywords}")

    chart_builder.generate_charts(global_summary_table, keywords=user_keywords)
    logger.info("Charts generated successfully.")


# -----------------------------------------------------------------------------------------
@routemanager.route("/regenerate_graphs", methods=["POST"])
def regenerate_graphs():
    """
    Handles regeneration of graphs when the user clicks the "Regenerate Graphs" button.
    Clears old charts, loads keywords from settings, and regenerates graphs.
    """
    logger.info("Entered regenerate_graphs function.")
    try:
        generate_charts_based_on_analysis()
        charts_folder = image_path + os.path.splitext(current_session_name)[0] + "/"

        # Fetch updated list of chart files
        chart_files = []
        if os.path.exists(charts_folder):
            chart_files = [
                f"images/{os.path.splitext(current_session_name)[0]}/{f}"
                for f in os.listdir(charts_folder)
                if f.endswith(".jpg") or f.endswith(".png")
            ]

        logger.info("Graphs regenerated successfully.")
        return render_template(
            "graphs.html",
            chart_files=chart_files,
            message="Graphs regenerated successfully!",
        )
    except Exception as e:
        logger.error(f"Error regenerating graphs: {e}", exc_info=True)
        return render_template(
            "graphs.html",
            chart_files=[],
            error_message=f"Error regenerating graphs: {str(e)}",
        )


# -----------------------------------------------------------------------------------------
@routemanager.route("/list_sessions", methods=["GET"])
def list_sessions():
    logger.info("Entered list_sessions function.")
    try:
        sessions = [f for f in os.listdir(sessions_path) if f.endswith(".pkl")]
        logger.debug(f"Found sessions: {sessions}")
        return render_template(
            "list_sessions.html",
            sessions=sessions,
            current_session_name=current_session_name,
        )
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        return render_template(
            "list_sessions.html",
            sessions=[],
            error_message=f"Failed to list sessions: {str(e)}",
            current_session_name=current_session_name,
        )


# -----------------------------------------------------------------------------------------
@routemanager.route("/load_session/<session_name>", methods=["POST"])
def load_session_by_name(session_name: str):
    logger.info(f"Entered load_session_by_name function for session: {session_name}")
    try:
        global survey_1_in_memory, survey_2_in_memory, global_summary_table, global_results, selected_theme, current_session_name, alpha, test_method, isNormalized
        
        session_path = sessions_path + session_name
        logger.info(f"Loading session from: {session_path}")
        state = load_session_state(session_path)

        survey_1_in_memory = state["survey_1"]
        survey_2_in_memory = state["survey_2"]
        global_summary_table = state["global_summary_table"]
        global_results = state.get("global_results", {})
        current_session_name = session_name
        isNormalized = state["isNormalized"]

        theme_name = state.get("selected_theme_name")
        selected_theme = next(
            (theme for theme in available_themes if theme.name == theme_name),
            selected_theme,
        )
        alpha = state.get("alpha", DEFAULT_ALPHA)
        test_method = state.get("test_method", DEFAULT_TEST_METHOD)

        logger.info("Regenerating charts for the loaded session.")
        generate_charts_based_on_analysis()

        logger.info(f"Session {session_name} loaded successfully.")
        return render_template(
            "list_sessions.html",
            sessions=os.listdir(sessions_path),
            message=f"Session {session_name} loaded successfully!",
            current_session_name=current_session_name,
        )
    except FileNotFoundError as e:
        logger.warning(f"FileNotFoundError: {e}")
        return render_template(
            "list_sessions.html",
            sessions=os.listdir(sessions_path),
            error_message=f"Error: {str(e)}",
            current_session_name=current_session_name,
        )
    except Exception as e:
        logger.error(f"Failed to load session: {e}", exc_info=True)
        return render_template(
            "list_sessions.html",
            sessions=os.listdir(sessions_path),
            error_message=f"Failed to load session: {str(e)}",
            current_session_name=current_session_name,
        )


# -----------------------------------------------------------------------------------------
def save_session():
    logger.info("Entered save_session function.")
    try:
        state = {
            "survey_1": survey_1_in_memory,
            "survey_2": survey_2_in_memory,
            "global_summary_table": (
                global_summary_table
                if global_summary_table is not None
                else pd.DataFrame()
            ),
            "global_results": global_results if global_results else {},
            "selected_theme_name": (
                selected_theme.name if selected_theme is not None else "default"
            ),
            "alpha": alpha if alpha is not None else DEFAULT_ALPHA,
            "test_method": test_method
            if test_method is not None
            else DEFAULT_TEST_METHOD,
            "isNormalized": isNormalized
        }

        save_path = sessions_path + current_session_name

        logger.debug(f"Saving session to path: {save_path}")
        save_session_state(state, save_path)
        logger.info("Session saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save session: {e}", exc_info=True)
        return render_template(
            "error.html", error_message=f"Failed to save state: {str(e)}"
        )


# -----------------------------------------------------------------------------------------
@routemanager.route("/update_session", methods=["POST"])
def update_session():
    logger.info("Entered update_session function.")
    try:
        session_path = sessions_path + current_session_name

        if os.path.exists(session_path):
            logger.debug(f"Loading existing session from path: {session_path}")
            state = load_session_state(session_path)
        else:
            logger.error("No active session found. Please start a new session.")
            raise ValueError("No active session found. Please start a new session.")

        if survey_1_in_memory is not None:
            state["survey_1"] = survey_1_in_memory
        if survey_2_in_memory is not None:
            state["survey_2"] = survey_2_in_memory
        if global_summary_table is not None:
            state["global_summary_table"] = global_summary_table
        if selected_theme is not None:
            state["selected_theme_name"] = selected_theme.name
        if alpha is not None:
            state["alpha"] = alpha
        if test_method is not None:
            state["test_method"] = test_method
            
        state["isNormalized"] = isNormalized

        logger.debug("Updating session state.")
        save_session_state(state, session_path)
        logger.info("Session updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update session: {e}", exc_info=True)
        return render_template(
            "error.html", error_message=f"Failed to update session: {str(e)}"
        )


# -----------------------------------------------------------------------------------------
@routemanager.route("/delete_session/<session_name>", methods=["DELETE"])
def delete_session(session_name: str):
    logger.info(f"Entered delete_session function for session: {session_name}")
    try:
        session_path = sessions_path + session_name
        if os.path.exists(session_path):
            logger.debug(f"Deleting session at path: {session_path}")
            os.remove(session_path)
            logger.info(f"Session {session_name} deleted successfully.")
            return {
                "success": True,
                "message": f"Session {session_name} deleted successfully!",
            }
        else:
            logger.warning(f"Session {session_name} not found.")
            return {"success": False, "error": "Session not found."}
    except Exception as e:
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        return {"success": False, "error": f"Failed to delete session: {str(e)}"}


# -----------------------------------------------------------------------------------------
@routemanager.route("/settings", methods=["GET"])
def settings():
    """
    Renders the settings page with available themes, the selected theme,
    and the stored keywords for chart analysis. Logs errors and provides fallback in case of issues.
    """
    logger.info("Entered settings function.")
    try:
        # Serialize available themes
        themes_serializable = [
            {"name": theme.name, "colors": list(theme.colors.values())}
            for theme in available_themes
        ]
        logger.debug("Serialized available themes.")

        # Serialize the selected theme
        selected_theme_serializable = None
        if selected_theme:
            selected_theme_serializable = {
                "name": selected_theme.name,
                "colors": list(selected_theme.colors.values()),
            }
            logger.debug("Serialized selected theme.")

        # Load stored keywords for chart analysis
        keywords = KeywordManager.load_keywords()
        logger.debug(f"Loaded {len(keywords)} keywords.")

        # Render the settings page
        logger.info("Rendering settings page with themes and keywords.")
        return render_template(
            "settings.html",
            themes=themes_serializable,
            selected_theme=selected_theme_serializable,
            keywords=keywords,
        )
    except Exception as error:
        logger.error("Failed to render settings page.", exc_info=True)
        return render_template(
            "error.html", error_message=f"Failed to load settings: {error}"
        )


# -----------------------------------------------------------------------------------------
@routemanager.route("/save_theme", methods=["POST"])
def save_theme():
    logger.info("Entered save_theme function.")
    global selected_theme
    try:
        theme_name = request.form.get("theme")
        logger.debug(f"Requested theme to save: {theme_name}")

        selected_theme = next(
            (theme for theme in available_themes if theme.name == theme_name), None
        )

        if selected_theme:
            message = "Theme changed."
            logger.info(f"Theme changed to: {selected_theme.name}")

            if global_summary_table is not None:
                logger.info("Regenerating charts based on the new theme.")
                generate_charts_based_on_analysis()

            if current_session_name:
                logger.info("Saving theme to the current session.")
                update_session()
                message = "Theme saved successfully."
        else:
            logger.warning("Failed to find the requested theme.")
            message = "Failed to save the theme. Please try again."

        # Load keywords before rendering the page again
        keywords = KeywordManager.load_keywords()
        logger.debug(f"Loaded keywords after saving theme: {keywords}")

        logger.info("Rendering settings page with updated theme and keywords.")
        return render_template(
            "settings.html",
            themes=[
                {"name": theme.name, "colors": list(theme.colors.values())}
                for theme in available_themes
            ],
            selected_theme=(
                {
                    "name": selected_theme.name,
                    "colors": list(selected_theme.colors.values()),
                }
                if selected_theme
                else None
            ),
            keywords=keywords,  # Ensure keywords are passed to the template
            message=message,
        )
    except Exception as e:
        logger.error(f"Failed to save theme: {e}", exc_info=True)
        return render_template(
            "error.html", error_message=f"Failed to save theme: {str(e)}"
        )


# -----------------------------------------------------------------------------------------
@routemanager.route("/save_keywords", methods=["POST"])
def save_keywords():
    keyword = request.form.get("keyword")
    if keyword:
        KeywordManager.add_keyword(keyword)
        logger.info(f"Added new keyword: {keyword}")

    return settings()


# -----------------------------------------------------------------------------------------
@routemanager.route("/delete_keyword/<keyword>", methods=["POST"])
def delete_keyword(keyword: str):
    KeywordManager.delete_keyword(keyword)
    logger.info(f"Deleted keyword: {keyword}")
    return settings()
