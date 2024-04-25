import random
from enum import Enum

with open("data/words_alpha.txt") as f:
    words = f.read().splitlines()

random.shuffle(words)

# Filter words with 5 characters
words = [word for word in words if len(word) == 5]


def not_in_word(letter, words):
    # Remove words that contain the letter
    return [word for word in words if letter not in word]


def in_word(letter, words):
    # Remove words that don't contain the letter
    return [word for word in words if letter in word]


def in_word_at_position(letter, position, words):
    # Remove words that don't have the letter at the position
    return [word for word in words if word[position] == letter]


def in_word_not_at_position(letter, position, words):
    # Remove words that have the letter at the position
    words = in_word(letter, words)
    return [word for word in words if word[position] != letter]


def get_guess():
    while True:
        guess = input("Enter a 5-letter word: ").lower()

        if len(guess) != 5:
            print("Word must be 5 letters long stupid")
            continue
        elif guess not in words:
            print("Word is not in the dictionary")
            continue
        elif guess in guesses:
            print("You already guessed that word")
            continue
        elif guess.isalpha() == False:
            print("Word must be alphabetic")
            continue
        else:
            break

    return guess


class LetterState(Enum):
    NOT_IN_WORD = 1
    IN_WORD_AT_POSITION = 2
    IN_WORD_NOT_AT_POSITION = 3


class Letter:
    def __init__(self, letter):
        self.letter = letter
        self.state = LetterState.NOT_IN_WORD

    def __str__(self):
        return f"{self.letter}, {self.state}"

    def __repr__(self):
        return f"{self.letter, self.state}"


guesses = []

secret_word = random.choice(words)
# print("Secret word:", secret_word)


def display_guess(guess):
    for letter in guess:
        if letter.state == LetterState.NOT_IN_WORD:
            print(f"\033[31m{letter.letter}\033[0m", end="")
        elif letter.state == LetterState.IN_WORD_AT_POSITION:
            print(f"\033[32m{letter.letter}\033[0m", end="")
        else:
            print(f"\033[33m{letter.letter}\033[0m", end="")
    print()


for i in range(0, 6):
    print(f"Guess {i}")
    guess_word = get_guess()

    if guess_word == secret_word:
        print("You win!")
        break

    guess = []

    for li, letter in enumerate(guess_word):
        curr_letter = Letter(letter)
        if secret_word[li] == letter:
            curr_letter.state = LetterState.IN_WORD_AT_POSITION
        elif letter in secret_word:
            curr_letter.state = LetterState.IN_WORD_NOT_AT_POSITION
        else:
            curr_letter.state = LetterState.NOT_IN_WORD

        guess.append(curr_letter)

    # Remove words that don't have the guessed letter at the guessed position
    for li, letter in enumerate(guess):
        if letter.state == LetterState.IN_WORD_AT_POSITION:
            words = in_word_at_position(letter.letter, li, words)
        elif letter.state == LetterState.IN_WORD_NOT_AT_POSITION:
            words = in_word_not_at_position(letter.letter, li, words)
        else:
            words = not_in_word(letter.letter, words)

    guesses.append(guess)
    print("Guesses:")
    for guess in guesses:
        display_guess(guess)
    print("Words left:", len(words))
    if len(words) > 50:
        print("Words:", words[:20])
    else:
        print("Words:", words)
