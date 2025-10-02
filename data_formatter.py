# Module: data_formatter.py
# Description: The `data_formatter.py` file contains a function `format_jobscan_result` that
# takes a dictionary as input and returns a list of dictionaries, each containing
# a label and parsed text for "Hard Skills" and "Soft Skills" extracted from the
# input dictionary.

def format_jobscan_result(result: dict) -> list[dict]:
    return [
        {
            "label": "Hard Skills",
            "parsed_text": result.get("hard_skills", "No hard skills found.")
        },
        {
            "label": "Soft Skills",
            "parsed_text": result.get("soft_skills", "No soft skills found.")
        }
    ]
