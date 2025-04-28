# CSV to Anki Vocabulary Converter

A Python script that converts CSV vocabulary files into Anki decks with audio pronunciation and example sentences.

## Features

- Converts CSV vocabulary lists to Anki decks
- Adds US English audio pronunciation for each word
- Highlights the word in example sentences (bold)
- Supports multiple examples per word
- Beautiful card formatting with clear sections

## Project Structure

```
.
├── csv_files/          # Place your vocabulary CSV files here
│   └── example.csv     # Example vocabulary file
├── anki_decks/         # Generated Anki decks will be here
├── temp_audio/         # Cached audio files (gitignored)
├── convert_csv_to_anki.py
└── requirements.txt
```

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
   pip install pandas genanki gTTS
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
