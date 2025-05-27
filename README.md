# Web-Based Wordle Game

This project is a web-based version of the popular word-guessing game, Wordle. It allows you to play the game in your browser, trying to guess a secret 5-letter word within six attempts. The application also provides feedback on your guesses and can suggest possible words based on the letters you've already tried.

## Features

*   Play Wordle in your web browser.
*   Get immediate feedback on your guesses with standard Wordle color-coding.
*   See the count of possible remaining words.
*   Get suggestions for your next guess.

## Setup Instructions

Follow these steps to set up and run the Wordle game on your local machine.

1.  **Clone the Repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a Virtual Environment (Recommended):**
    It's good practice to create a virtual environment to manage project dependencies.
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install Dependencies:**
    Install the necessary Python packages using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

Once the setup is complete, you can run the FastAPI application using Uvicorn:

```bash
uvicorn main:app --reload
```

The `--reload` flag enables auto-reloading, so the server will restart automatically when you make changes to the code.

After running the command, the application will be accessible at:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

Open this URL in your web browser to play the game.

## How to Play

The game follows the standard Wordle rules:

1.  **Objective:** Guess the secret 5-letter word in 6 tries.
2.  **Making a Guess:** Enter your 5-letter guess into the input field and submit.
3.  **Feedback Colors:**
    *   **Green:** The letter is in the word and in the correct position.
    *   **Yellow:** The letter is in the word but in the wrong position.
    *   **Gray:** The letter is not in the word at all.

Use the feedback to refine your subsequent guesses. Good luck!
