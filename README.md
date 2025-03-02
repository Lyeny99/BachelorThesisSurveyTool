# Survey Analysis Application

## Overview
This application provides a comprehensive solution for analyzing survey data, comparing results, and generating meaningful visualizations. Built with Flask, Python, and leveraging libraries like Pandas, Matplotlib, and Loguru, this project is designed to streamline survey data processing and statistical analysis.

## Features
- **Data Processing**: Convert raw survey data into a structured format.
- **Hypothesis Testing**: Perform statistical tests (e.g., t-test, Wilcoxon) on survey results.
- **Visualization**: Generate bar charts and other visual aids for data comparison.
- **Color Schemes**: Apply customizable color schemes to charts.
- **Session Management**: Save and load analysis sessions.
- **Logging**: Detailed application logs using Loguru.

## Project Structure
```
.
├── src
│   ├── models
│   │   ├── question.py             # Question model
│   │   ├── result.py               # Result and Answer models
│   │   └── survey.py               # Survey model
│   │   └── keywords.py             # Class for Keywords
│   │   └── color_scheme.py         # Color Scheme model
│   ├── utils
│   │   ├── answer_processor.py     # Processes answers to standard formats
│   │   ├── chart_builder.py        # Generates charts
│   │   ├── data_preparer.py        # Matches and processes questions
│   │   ├── session_manager.py      # Handles session saving/loading
│   │   └── analysis.py             # Performs statistical analysis
│   ├── blueprints
│   │   ├── routemanager.py         # Handles application routes
│   │   └── templates
│   │       ├── analysis.html       # Analysis results page
│   │       ├── base.html           # Base template for layouts
│   │       ├── data.html           # Data overview page
│   │       ├── error.html          # Error display page
│   │       ├── general.html        # General overview page
│   │       ├── graphs.html         # Visualization page
│   │       ├── list_sessions.html  # Session management page
│   │       ├── settings.html       # Settings for color schemes
│   │       └── survey.html         # Survey upload and selection
├── static
│   ├── color_schemes               # JSON files for custom color schemes
│   ├── sessions                    # Saved sessions
│   ├── logs                        # Log File
│   └── images                      # Generated chart images
├── app.py                          # Flask application entry point
├── appsettings.json                # configuration
└── README.md                       # Project documentation
```

## Getting Started

### Prerequisites
- Python 3.8+
- Pip (Python package manager)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd survey-analysis
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the folder structure:
   ```bash
   mkdir -p static/images static/color_schemes
   ```

4. Add color scheme JSON files to `static/color_schemes` (optional).

### Running the Application
```bash
python app.py
```
Access the application at `http://localhost:5000`.

## Usage
1. **Upload Surveys**: Upload two survey CSV files via the `/survey` route.
2. **Perform Analysis**: Navigate to the `/analysis` route and specify test parameters.
3. **View Results**: Access the `/graphs` route to visualize results.
4. **Customize Settings**: Adjust chart color schemes in the `/settings` route.

## Key Components

### Models
- **Survey**: Represents survey metadata, questions, results, and responses.
- **Question**: Handles individual survey questions.
- **Result**: Tracks participant responses.
- **ColorScheme**: Represents color schmes for Charts

### Utilities
- **AnswerProcessor**: Standardizes and processes survey answers.
- **DataPreparer**: Matches and processes survey questions for comparison.
- **ChartBuilder**: Generates visualizations based on survey data.
- **SessionManager**: Saves and loads session states for continuity.
- **Analysis**: Performs statistical hypothesis testing.

## Logging
Logs are implemented using Loguru and stored in the `logs` directory. Logging includes:
- Information on major actions (e.g., data processing, chart generation).
- Debug-level details for troubleshooting.

## Theme
Start Bootstrap LLC is providing the SB Admin 2 Bootstrap theme, which is used for this project.
Theme can be checked out at: https://startbootstrap.com/theme/sb-admin-2

## Contributing
1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit changes:
   ```bash
   git commit -m "Add new feature"
   ```
4. Push to your branch and create a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- [Pandas](https://pandas.pydata.org/)
- [Matplotlib](https://matplotlib.org/)
- [Loguru](https://github.com/Delgan/loguru)
- [SB Admin 2](https://github.com/startbootstrap/startbootstrap-sb-admin-2)
