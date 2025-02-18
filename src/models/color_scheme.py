import json
import os
from loguru import logger


class ColorScheme:
    """
    Represents a color scheme with a name and a set of colors.

    Attributes:
        name (str): The name of the color scheme.
        colors (dict): A dictionary of colors, with keys as "color1", "color2", etc.
    """

    def __init__(self, name: str, colors: dict[str, str]):
        """
        Initializes a ColorScheme instance.

        Parameters:
            name (str): The name of the color scheme.
            colors (dict): A dictionary of color values, with keys like "color1", "color2", etc.
        """
        logger.debug(f"Initializing ColorScheme: name={name}")
        self.name = name
        self.colors = colors

    @staticmethod
    def load_schemes(directory: str = "static/color_schemes/"):
        """
        Loads all color schemes from JSON files in the specified directory.

        Each JSON file should contain a dictionary of color values. The function renames colors
        to follow a "color1", "color2", etc., format, and creates a ColorScheme instance for each file.

        Parameters:
            directory (str): The directory containing color scheme JSON files (default is "static/color_schemes").

        Returns:
            list of ColorScheme: A list of ColorScheme instances loaded from the directory.
        """
        logger.info(f"Loading color schemes from directory: {directory}")
        schemes = []
        try:
            if not os.path.exists(directory):
                logger.warning(f"Directory does not exist: {directory}")
                return schemes

            for filename in os.listdir(directory):
                if filename.endswith(".json"):
                    filepath = directory + filename
                    logger.debug(f"Processing file: {filepath}")
                    try:
                        with open(filepath, encoding="utf-8") as f:
                            colors = json.load(f)
                            colors = {
                                f"color{i+1}": color
                                for i, color in enumerate(colors.values())
                            }
                            name = os.path.splitext(filename)[0]
                            schemes.append(ColorScheme(name=name, colors=colors))
                            logger.info(f"Loaded color scheme: {name}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON file {filepath}: {e}")
                    except Exception as e:
                        logger.error(
                            f"Unexpected error processing file {filepath}: {e}"
                        )

            logger.info(f"Total color schemes loaded: {len(schemes)}")
        except Exception as e:
            logger.error(f"Failed to load color schemes: {e}", exc_info=True)

        return schemes
