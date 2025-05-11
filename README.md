# CSV to Anki Converter

A Python script to convert CSV vocabulary files into Anki decks with audio pronunciation and special word highlighting.

## Features

- Converts CSV files to Anki decks
- Adds audio pronunciation using Google Text-to-Speech
- Formats example sentences with bold target words
- Supports multiple example sentences per word
- Optional highlighting of special/frequent words in red
- Processes single files or entire directories

## Installation

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd csv-to-anki
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Create your vocabulary CSV file in the `csv_files` directory using this format:
   ```
   word | part_of_speech meaning | example1 | example2 | example3
   ```
   Example:
   ```
   abate | v. to decrease; reduce | The storm gradually abated.
   ```

2. Run the script:
   ```bash
   python convert_csv_to_anki.py
   ```

3. Find your generated Anki decks in the `anki_decks` directory

4. Import the `.apkg` files into Anki

## Card Format

### Front
- Word
- Audio pronunciation button

### Back
- Word
- Audio pronunciation button
- Meaning
- Example sentences with the word in **bold**

## Notes

- Uses `|` as the CSV separator
- First column must be the word
- Second column must be the meaning
- Additional columns are treated as examples
- Audio files are cached to avoid regeneration
- Multiple CSV files in `csv_files` will all be processed
