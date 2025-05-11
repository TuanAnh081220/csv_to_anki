import csv
import os
import random
import re
from typing import List, Dict, Tuple
import genanki
import argparse


def extract_usage(example: str) -> Tuple[str, str]:
    """
    Extract the usage part from the example and return both the usage and the example without the usage.
    """
    # Find text between <strong> tags
    match = re.search(r"<strong>(.*?)</strong>", example)
    if not match:
        return "", example

    usage = match.group(1)
    # Remove the <strong> tags from the example
    example_without_usage = example.replace(f"<strong>{usage}</strong>", "_____")
    return usage, example_without_usage


def read_magoosh_words(csv_file: str) -> List[Dict]:
    """
    Read the magoosh basic words CSV file and return a list of dictionaries
    containing word, form (part of speech), meaning, example, and usage.
    """
    words = []
    with open(csv_file, "r", encoding="utf-8") as f:
        for line in f:
            # Split by | character
            parts = line.strip().split("|")
            if len(parts) != 3:
                print("invalid line: ", line)
                continue
            word, definition, example = parts

            # Split definition into form and meaning
            form_meaning = definition.split(". ", 1)
            if len(form_meaning) != 2:
                print(f"Invalid definition format for word '{word}': {definition}")
                continue

            form, meaning = form_meaning

            # Extract usage from example
            usage, example_without_usage = extract_usage(example)

            words.append(
                {
                    "word": word,
                    "form": form,
                    "meaning": meaning,
                    "example": example_without_usage,
                    "usage": usage,
                }
            )
    return words


def create_multiple_choice(word: Dict, all_words: List[Dict]) -> List[Dict]:
    """
    Create a multiple choice question with 4 options including the correct answer.
    All options will have the same part of speech as the correct answer.
    Returns a list of dictionaries containing word and its information.
    """
    # Get all other words with the same form except the current one
    other_words = [
        w for w in all_words if w["word"] != word["word"] and w["form"] == word["form"]
    ]

    # If we don't have enough words with the same form, print a warning
    if len(other_words) < 3:
        print(
            f"Warning: Not enough words with form '{word['form']}' for word '{word['word']}'"
        )
        # Get all other words regardless of form
        other_words = [w for w in all_words if w["word"] != word["word"]]

    # Randomly select 3 other words
    options = random.sample(other_words, 3)

    # Add the correct answer
    options.append(word)

    # Shuffle the options
    random.shuffle(options)

    return options


def create_anki_cards(words: List[Dict]) -> List[Dict]:
    """
    Create Anki cards with multiple choice questions.
    """
    # Shuffle the words list before creating cards
    random.shuffle(words)

    cards = []
    for word_idx, word in enumerate(words):
        options = create_multiple_choice(word, words)

        # Create the front card with the example and options using HTML formatting
        front = f'<div class="question">{word["example"]}</div>\n'
        front += '<div class="options">\n'
        for i, option in enumerate(options, 1):
            front += f'<div class="option"><input type="radio" name="answer" id="option_{word_idx}_{i}" class="option-radio" data-option="{i}" data-word="{option["word"]}"><label for="option_{word_idx}_{i}">{i}. {option["word"]}</label></div>\n'
        front += "</div>"
        # Add JavaScript to handle radio button states and answer checking
        front += """
<script>
(function() {
    // Function to save radio button state
    function saveRadioState() {
        const selectedRadio = document.querySelector('input[name="answer"]:checked');
        if (selectedRadio) {
            localStorage.setItem('selectedOption', selectedRadio.id);
            localStorage.setItem('selectedWord', selectedRadio.dataset.word);
        }
    }

    // Function to restore radio button state
    function restoreRadioState() {
        const savedOption = localStorage.getItem('selectedOption');
        if (savedOption) {
            const radio = document.getElementById(savedOption);
            if (radio) {
                radio.checked = true;
            }
        }
    }

    // Add event listeners to radio buttons
    document.querySelectorAll('.option-radio').forEach(radio => {
        radio.addEventListener('change', saveRadioState);
    });

    // Restore state when the card is shown
    restoreRadioState();
})();
</script>
"""

        # Create the back card with information about all options
        back = '<div class="answer-feedback"></div>\n'
        back += '<div class="correct-answer">\n'
        back += "<h3>Correct Answer</h3>\n"
        # Find and show the correct answer first
        correct_option = next(opt for opt in options if opt["word"] == word["word"])
        back += f'<div class="word">{correct_option["word"]} <span class="form">({correct_option["form"]})</span></div>\n'
        back += f'<div class="meaning">Meaning: {correct_option["meaning"]}</div>\n'
        usage = correct_option["usage"]
        back += f'<div class="example">Example: {correct_option["example"].replace("_____", f"<strong>{usage}</strong>")}</div>\n'
        back += "</div>\n\n"

        back += '<div class="other-options">\n'
        back += "<details>\n"
        back += "<summary>Click to show other options</summary>\n"
        # Show other options
        for i, option in enumerate(options, 1):
            if option["word"] != word["word"]:
                back += f'<div class="option-detail">\n'
                back += f'<div class="word">{i}. {option["word"]} <span class="form">({option["form"]})</span></div>\n'
                back += f'<div class="meaning">Meaning: {option["meaning"]}</div>\n'
                usage = option["usage"]
                back += f'<div class="example">Example: {option["example"].replace("_____", f"<strong>{usage}</strong>")}</div>\n'
                back += "</div>\n"
        back += "</details>\n"
        back += "</div>"

        # Add JavaScript to check the answer
        back += (
            '''
<script>
(function() {
    const correctWord = "'''
            + word["word"]
            + """";
    const selectedWord = localStorage.getItem('selectedWord');
    const feedbackDiv = document.querySelector('.answer-feedback');
    
    if (selectedWord === correctWord) {
        feedbackDiv.className = 'answer-feedback correct';
        feedbackDiv.textContent = '✓ Correct!';
    } else {
        feedbackDiv.className = 'answer-feedback incorrect';
        feedbackDiv.textContent = '✗ Incorrect';
    }
})();
</script>
"""
        )

        cards.append({"front": front, "back": back})

    return cards


def export_to_anki(deck_name: str, cards: List[Dict], output_path: str):
    """
    Export the cards to an Anki deck using genanki.
    """
    model = genanki.Model(
        1607392319,
        deck_name,
        fields=[
            {"name": "Front"},
            {"name": "Back"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
            },
        ],
        css="""
            .card {
                font-family: arial;
                font-size: 18px;
                text-align: left;
                color: #222;
                background-color: #fff;
                padding: 20px;
                line-height: 1.5;
            }
            .question {
                font-size: 20px;
                margin-bottom: 20px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
            .options {
                margin-top: 20px;
            }
            .option {
                margin: 10px 0;
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                display: flex;
                align-items: center;
            }
            .option:hover {
                background-color: #f0f0f0;
            }
            .option-radio {
                margin-right: 10px;
                width: 18px;
                height: 18px;
                cursor: pointer;
            }
            .option label {
                cursor: pointer;
                flex-grow: 1;
            }
            .answer-feedback {
                margin-bottom: 20px;
                padding: 15px;
                border-radius: 5px;
                font-size: 20px;
                font-weight: bold;
                text-align: center;
            }
            .answer-feedback.correct {
                background-color: #e8f5e9;
                color: #2e7d32;
                border: 2px solid #2e7d32;
            }
            .answer-feedback.incorrect {
                background-color: #ffebee;
                color: #c62828;
                border: 2px solid #c62828;
            }
            .correct-answer {
                margin-bottom: 20px;
                padding: 15px;
                background-color: #e8f5e9;
                border-radius: 5px;
            }
            .correct-answer h3 {
                margin: 0 0 10px 0;
                color: #2e7d32;
            }
            .word {
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 8px;
            }
            .form {
                color: #666;
                font-size: 16px;
                font-weight: normal;
            }
            .meaning {
                margin-bottom: 8px;
            }
            .example {
                font-style: italic;
            }
            .other-options {
                margin-top: 20px;
            }
            .other-options h3 {
                margin: 0 0 10px 0;
                color: #666;
            }
            details {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
            }
            summary {
                cursor: pointer;
                padding: 5px;
                color: #0077cc;
            }
            summary:hover {
                background-color: #f0f0f0;
            }
            .option-detail {
                margin: 15px 0;
                padding: 10px;
                border-left: 3px solid #e0e0e0;
            }
            strong { 
                color: #0077cc;
                font-weight: bold;
            }
            hr {
                margin: 20px 0;
                border: none;
                border-top: 1px solid #ccc;
            }
        """,
    )

    deck = genanki.Deck(2059400110, deck_name)

    for card in cards:
        note = genanki.Note(model=model, fields=[card["front"], card["back"]])
        deck.add_note(note)

    genanki.Package(deck).write_to_file(output_path)
    print(f"Anki deck exported to {output_path}")


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Create Anki cards from a CSV file of words."
    )
    parser.add_argument(
        "csv_name",
        help="Name of the CSV file (without extension) in the csv_files directory",
    )
    args = parser.parse_args()

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct path to the CSV file
    csv_file = os.path.join(script_dir, "csv_files", f"{args.csv_name}.csv")

    # Read the words
    words = read_magoosh_words(csv_file)

    # Create Anki cards
    cards = create_anki_cards(words)

    # Print first few cards to verify
    print(f"Created {len(cards)} cards")

    # Export to Anki deck in anki_decks folder
    anki_decks_dir = os.path.join(script_dir, "anki_decks")
    if not os.path.exists(anki_decks_dir):
        os.makedirs(anki_decks_dir)
    deck_name = f"{args.csv_name}_qna"
    output_path = os.path.join(anki_decks_dir, f"{deck_name}.apkg")
    export_to_anki(deck_name, cards, output_path)


if __name__ == "__main__":
    main()
