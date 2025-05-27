from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from enum import Enum
import random
from typing import List, Dict, Optional
import os

# --- Enums and Pydantic Models ---

class LetterState(str, Enum):
    NOT_IN_WORD = "not_in_word"  # Letter is not in the secret word
    IN_WORD_WRONG_POSITION = "in_word_wrong_position"  # Letter is in the word but in the wrong spot
    IN_WORD_CORRECT_POSITION = "in_word_correct_position"  # Letter is in the word and in the correct spot

class LetterFeedback(BaseModel):
    letter: str
    state: LetterState

class GuessInput(BaseModel):
    guess: str = Field(..., min_length=5, max_length=5, description="A 5-letter guess")

class GameStatusResponse(BaseModel):
    guess_feedback: Optional[List[LetterFeedback]] = None
    possible_words_count: int
    suggestions: Optional[List[str]] = None
    game_won: bool = False
    message: Optional[str] = None

# --- FastAPI App Initialization ---
app = FastAPI(title="Wordle Helper API")

# Mount static files
# Ensure a 'static' directory exists in the same directory as main.py
# For development, it's fine. For production, consider a more robust setup.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Check if static directory exists, create if not (useful for some environments)
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
    print(f"Created static directory at: {STATIC_DIR}")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- Word List Loading ---
DATA_DIR = os.path.join(BASE_DIR, "data")
WORD_LIST_FILE = os.path.join(DATA_DIR, "words_alpha.txt")

# --- Global Variables ---
original_words_full_list: List[str] = []
current_secret_word: Optional[str] = None
current_possible_words: List[str] = []

# --- Helper Functions ---

def load_words():
    """
    Loads words from data/words_alpha.txt into original_words_full_list.
    Raises RuntimeError if the file is not found or is empty.
    """
    global original_words_full_list, current_possible_words
    if not os.path.exists(WORD_LIST_FILE):
        raise RuntimeError(f"Word list file not found: {WORD_LIST_FILE}")

    with open(WORD_LIST_FILE, "r") as f:
        loaded_words = [line.strip().lower() for line in f if len(line.strip()) == 5 and line.strip().isalpha()]

    if not loaded_words:
        raise RuntimeError(f"No 5-letter words found in {WORD_LIST_FILE} or file is empty.")

    original_words_full_list = loaded_words
    current_possible_words = list(original_words_full_list)
    print(f"Successfully loaded {len(original_words_full_list)} words from {WORD_LIST_FILE}.")


# --- Application Startup Event ---
@app.on_event("startup")
async def startup_event():
    try:
        load_words()
    except RuntimeError as e:
        print(f"CRITICAL ERROR during startup: {e}")
        # Depending on the server, this might require manual intervention or a more graceful shutdown.
        # For Uvicorn, it will typically log the error and the app might not start correctly.
        raise  # Re-raise the exception to ensure FastAPI knows startup failed.


# --- API Endpoints ---

@app.post("/game/start", response_model=GameStatusResponse)
async def start_game():
    """
    Starts a new game by selecting a new secret word and resetting possible words.
    """
    global current_secret_word, current_possible_words
    if not original_words_full_list:
        raise HTTPException(status_code=500, detail="Word list not loaded. Cannot start game.")

    current_secret_word = random.choice(original_words_full_list)
    current_possible_words = list(original_words_full_list) # Reset to full list

    print(f"New game started. Secret word (for debugging): {current_secret_word}")

    return GameStatusResponse(
        possible_words_count=len(current_possible_words),
        suggestions=random.sample(current_possible_words, min(5, len(current_possible_words))),
        message="New game started. Make your first guess!"
    )

@app.post("/game/guess", response_model=GameStatusResponse)
async def make_guess(guess_input: GuessInput):
    """
    Processes a guess, provides feedback, and updates the list of possible words.
    """
    global current_secret_word, current_possible_words

    if not current_secret_word:
        raise HTTPException(status_code=400, detail="Game not started. Please start a new game first via POST /game/start.")

    guess = guess_input.guess.lower()

    if len(guess) != 5: # Redundant due to Pydantic, but good for explicit check
        raise HTTPException(status_code=422, detail="Guess must be exactly 5 letters long.")

    # Basic validation: check if the guess is a known word (optional for now, can be stricter)
    # For now, we allow any 5-letter string as per requirements, full validation later.
    # if guess not in original_words_full_list:
    #     raise HTTPException(status_code=422, detail="Guess is not a valid word.")

    feedback: List[LetterFeedback] = []
    temp_secret_word = list(current_secret_word) # mutable copy for checking letter occurrences

    game_won = (guess == current_secret_word)

    # Generate feedback for the guess
    feedback: List[LetterFeedback] = []
    game_won = (guess == current_secret_word)

    # Use a copy of the secret word to handle letter counts for duplicates (e.g., if secret is "APPLE" and guess is "POPPY")
    secret_word_letter_counts = {}
    for letter in current_secret_word:
        secret_word_letter_counts[letter] = secret_word_letter_counts.get(letter, 0) + 1
    
    # Step 1: Identify GREEN letters (correct letter, correct position)
    temp_feedback = [LetterFeedback(letter="", state=LetterState.NOT_IN_WORD)] * 5 # Initialize with default
    
    for i in range(5):
        letter = guess[i]
        if letter == current_secret_word[i]:
            temp_feedback[i] = LetterFeedback(letter=letter, state=LetterState.IN_WORD_CORRECT_POSITION)
            secret_word_letter_counts[letter] -= 1 # Account for this used letter
        else:
            # Placeholder, will be determined in next step
            temp_feedback[i] = LetterFeedback(letter=letter, state=LetterState.NOT_IN_WORD) # Tentative

    # Step 2: Identify YELLOW letters (correct letter, wrong position) and GRAY letters
    for i in range(5):
        if temp_feedback[i].state == LetterState.IN_WORD_CORRECT_POSITION:
            continue # Already processed as green

        letter = guess[i]
        # Check if this letter is present elsewhere in the secret word (and not already used up by a green)
        if secret_word_letter_counts.get(letter, 0) > 0:
            temp_feedback[i] = LetterFeedback(letter=letter, state=LetterState.IN_WORD_WRONG_POSITION)
            secret_word_letter_counts[letter] -= 1 # Account for this used letter
        else:
            temp_feedback[i] = LetterFeedback(letter=letter, state=LetterState.NOT_IN_WORD)
    
    feedback = temp_feedback

    # Filter current_possible_words based on the generated feedback
    new_possible_words = []
    for word in current_possible_words:
        possible = True
        # Create a mutable copy of secret word letter counts for each word check,
        # or rather, check against the properties derived from the feedback.
        
        # Rule: For each letter in the guess and its feedback:
        for i in range(5):
            guess_char = feedback[i].letter
            state = feedback[i].state
            
            if state == LetterState.IN_WORD_CORRECT_POSITION:
                if word[i] != guess_char:
                    possible = False
                    break
            elif state == LetterState.IN_WORD_WRONG_POSITION:
                if guess_char not in word or word[i] == guess_char:
                    possible = False
                    break
            elif state == LetterState.NOT_IN_WORD:
                # A gray letter means this specific instance of the letter is not in the word
                # in a way that isn't already accounted for by green/yellow.
                # Count how many times guess_char appears as green or yellow in the *guess*
                num_green_yellow_occurrences_in_guess = 0
                for fb_inner in feedback:
                    if fb_inner.letter == guess_char and \
                       (fb_inner.state == LetterState.IN_WORD_CORRECT_POSITION or \
                        fb_inner.state == LetterState.IN_WORD_WRONG_POSITION):
                        num_green_yellow_occurrences_in_guess += 1
                
                # If the count of this char in the potential word is greater than
                # the number of times it was marked green/yellow in the guess, then this word is not possible.
                # Also, if the letter at this specific position in the word is the gray letter, it's not possible
                # (unless this rule is superseded by a yellow/green for the same letter from another position in the guess)
                if word.count(guess_char) > num_green_yellow_occurrences_in_guess:
                    possible = False
                    break
                if word[i] == guess_char and num_green_yellow_occurrences_in_guess == 0 : # if it is gray, and no other instance is yellow/green
                     possible = False # then this letter cannot be at this position.
                     break


        if possible:
            # Additional check for yellow letters to ensure the minimum count is met
            # For every yellow letter in the guess, the word must contain at least that many
            # (plus any green ones of the same letter).
            # Example: Guess "SASSY", Secret "APPLE". S1 (yellow), S3 (gray). Word "PASSES" should be invalid.
            # Word "SHEEP". Secret "PLATE". Guess "STEAL". S(Y), T(Y), E(Y), A(G), L(G).
            # Word "SHEEP" should be invalid because A and L are not in it.
            # Word "TEASE" for secret "PLATE" from guess "STEAL":
            # T(Y): T in TEASE. TEASE[0]!=T. OK.
            # E(Y): E in TEASE. TEASE[1]!=E. OK.
            # A(G): TEASE[2]==A. OK.
            # S(Y): S in TEASE. TEASE[3]!=S. OK.
            # L(G): TEASE[4]==L. OK.
            # This seems mostly covered by the above. The NOT_IN_WORD rule is the most complex.
            # Let's ensure that if a letter is yellow, it must be in the word.
            # And if it's gray, it must not be in the word *more than* its green/yellow count in the guess.
            # This is handled by the existing IN_WORD_WRONG_POSITION and NOT_IN_WORD logic.
            new_possible_words.append(word)

    current_possible_words = list(set(new_possible_words))

    return GameStatusResponse(
        guess_feedback=feedback,
        possible_words_count=len(current_possible_words),
        suggestions=random.sample(current_possible_words, min(5, len(current_possible_words))) if current_possible_words else [],
        game_won=game_won,
        message="Guess processed." if not game_won else "Congratulations! You guessed the word!"
    )

if __name__ == "__main__":
    import uvicorn
    # To run: python main.py
    # Then access via browser or curl, e.g.:
    # curl -X POST http://127.0.0.1:8000/game/start
    # curl -X POST -H "Content-Type: application/json" -d '{"guess":"apple"}' http://127.0.0.1:8000/game/guess


# --- HTML Serving Endpoint ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Path to index.html. Adjust if your index.html is not in the root or a 'templates' folder.
    # For this setup, index.html is expected to be in the root directory alongside main.py
    index_html_path = os.path.join(BASE_DIR, "index.html")
    
    if not os.path.exists(index_html_path):
        print(f"Error: index.html not found at {index_html_path}")
        raise HTTPException(status_code=404, detail="index.html not found. Please ensure it is in the root directory.")
        
    with open(index_html_path, "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    try:
        load_words() 
        if not original_words_full_list:
             print("CRITICAL: No words available to run the application. The list is empty after loading attempt.")
        else:
            print(f"Starting Uvicorn server. {len(original_words_full_list)} words loaded.")
            print(f"Static directory: {STATIC_DIR}")
            print(f"Data directory: {DATA_DIR}")
            print(f"Word list file: {WORD_LIST_FILE}")
            print(f"Index.html expected at: {os.path.join(BASE_DIR, 'index.html')}")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except RuntimeError as e:
        print(f"Failed to start application: {e}")

# End of main.py
