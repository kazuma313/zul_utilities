def setup_logger():
    """Sets up a basic console logger."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def create_gemini_client(api_key: str, logger: logging.Logger) -> genai.Client | None:
    """
    Initializes and returns a Gemini client.

    Args:
        api_key (str): Your Google API key.
        logger (logging.Logger): The logger instance.

    Returns:
        genai.Client | None: An initialized client object, or None if creation fails.
    """
    if not api_key:
        logger.critical("Google API key is missing. Cannot create client.")
        return None
    try:
        logger.info("Initializing Gemini client...")
        client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialized successfully.")
        return client
    except Exception as e:
        logger.error("Failed to initialize Gemini client.", exc_info=True)
        return None
    

def process_pdf_with_gemini(
    client: genai.Client, 
    pdf_path: str, 
    prompt: str, 
    logger: logging.Logger,
    model_name: str = "gemini-2.5-pro"
) -> str | None:
    """
    Uses a pre-initialized Gemini client to process a PDF.

    Args:
        client (genai.Client): An active and initialized Gemini client instance.
        pdf_path (str): The local file path to the PDF.
        prompt (str): The prompt to send to the model.
        logger (logging.Logger): The logger instance for output.
        model_name (str, optional): The Gemini model to use. Defaults to "gemini-2.5-pro".

    Returns:
        str | None: The generated text content, or None if an error occurs.
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at path: {pdf_path}")
        return None

    uploaded_file = None
    try:
        file_basename = os.path.basename(pdf_path)
        logger.info(f"Uploading file: '{file_basename}'...")
        uploaded_file = client.files.upload(file=pdf_path)
        logger.info(f"File uploaded successfully. URI: {uploaded_file.uri}")

        logger.info(f"Sending request to Gemini model '{model_name}'...")
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, uploaded_file],
        )
        logger.info("Response received successfully.")
        return response.text

    except Exception as e:
        logger.error("An error occurred during the PDF processing workflow.", exc_info=True)
        return None
    
    finally:
        # Cleanup is still part of the process
        if uploaded_file:
            logger.info(f"Deleting uploaded file from server: {uploaded_file.name}...")
            try:
                client.files.delete(name=uploaded_file.name)
                logger.info("File cleanup complete.")
            except Exception:
                logger.error(f"Failed to delete file {uploaded_file.name}.", exc_info=True)


if __name__ == "__main__":
    import os
    logger = setup_logger()
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    client = create_gemini_client(api_key=GOOGLE_API_KEY, 
                                logger=logger)
    
    OCR_PROMPT = "Extract the text content from this PDF and return it in markdown format."
    pdf_path_1 = "path/to/your/document.pdf"
    response = process_pdf_with_gemini(
                client=client,
                pdf_path=pdf_path_1,
                prompt=OCR_PROMPT,
                model_name="gemini-2.5-pro",
                logger=logger
            )