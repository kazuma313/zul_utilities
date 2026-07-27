import os
import pandas as pd

def save_text_to_md(text_result: str, filename: str):
    """
    Save the given text to a markdown file with the specified filename.

    :param text_result: The text content to save.
    :param filename: The name of the file (without extension) to save the content to.
    """
    # Ensure the 'data' directory exists
    os.makedirs("data", exist_ok=True)

    # Create the full file path
    file_path = os.path.join("data", rf"{filename}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_result)


def save_latency_to_csv(mappinging: dict, file_name:str ="query_latency_recursive_results"):
    """
    Save latency data to a CSV file.

    :param retrieve_short: List of latencies for short queries.
    :param retrieve_medium: List of latencies for medium queries.
    :param retrieve_long: List of latencies for long queries.
    :param retrieve_extra_long: List of latencies for extra long queries.
    """
    # Ensure the 'data' directory exists
    os.makedirs("data", exist_ok=True)
    
    # Create dictionary with latency data

    # Convert to DataFrame
    df_latency = pd.DataFrame(mappinging)

    # Save to CSV
    df_latency.to_csv(f'{file_name}.csv', index=False)