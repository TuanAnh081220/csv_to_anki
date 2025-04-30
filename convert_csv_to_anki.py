import os
import pandas as pd
import genanki
from pathlib import Path
from gtts import gTTS
import tempfile


def generate_audio(word):
    """Generate audio file for a word using gTTS with US English"""
    try:
        # Create a temporary file
        temp_dir = Path('temp_audio')
        temp_dir.mkdir(exist_ok=True)
        
        audio_path = temp_dir / f"{word}.mp3"
        
        # Only generate if not already exists
        if not audio_path.exists():
            # Use US English (en-us) for pronunciation
            tts = gTTS(text=word, lang='en', tld='com')
            tts.save(str(audio_path))
        
        return audio_path
    except Exception as e:
        print(f"Warning: Could not generate audio for word '{word}': {e}")
        return None

def read_special_words(special_words_file):
    """Read special words from file and return as a set"""
    if not special_words_file:
        return set()
        
    special_words = set()
    try:
        with open(special_words_file, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:  # Skip empty lines
                    special_words.add(word.lower())
    except Exception as e:
        print(f"Warning: Could not read special words file: {e}")
    return special_words

def convert_csv_to_anki(csv_path, special_words=None):
    # Check if file is empty
    if os.path.getsize(csv_path) == 0:
        print(f"Warning: {csv_path} is empty")
        return None

    try:
        # Read the file line by line to handle variable number of fields
        rows = []
        max_fields = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Split by | and strip whitespace
                fields = [field.strip() for field in line.strip().split('|')]
                
                # Skip empty lines
                if not fields or not any(fields):
                    continue
                
                # Update max fields count
                max_fields = max(max_fields, len(fields))
                rows.append(fields)
        
        # Create DataFrame with proper number of columns
        df = pd.DataFrame(rows)
        
        # Pad rows with fewer fields with empty strings
        df = df.fillna('')
        
        # Check if DataFrame is empty
        if df.empty:
            print(f"Warning: No data found in {csv_path}")
            return None
        
        # First column is word, second is meaning, rest are examples
        df.columns = ['Word', 'Meaning'] + [f'Example_{i}' for i in range(len(df.columns)-2)]
    except pd.errors.EmptyDataError:
        print(f"Warning: {csv_path} has no data")
        return None
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return None

    # Define model (basic front/back)
    css = '''
    .card {
        font-family: Arial, sans-serif;
        font-size: 16px;
        text-align: left;
        color: black;
        background-color: white;
        padding: 20px;
    }
    .word {
        font-size: 28px;
        text-align: center;
        color: #2c3e50;
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 18px;
        font-weight: bold;
        color: #34495e;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    .meaning {
        font-size: 16px;
        margin-bottom: 20px;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    .examples {
        font-style: italic;
        color: #444;
        margin-left: 20px;
    }
    '''

    model = genanki.Model(
        1607392319,
        'Vocabulary Model',
        fields=[
            {'name': 'Word'},
            {'name': 'Meaning'},
            {'name': 'Example'},
            {'name': 'Audio'}
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '''
<div class="word">{{Word}}</div>
{{Audio}}
''',
                'afmt': '''
<div class="word">{{Word}}</div>
{{Audio}}
<hr id="answer">
<div class="section-title">Meaning:</div>
<div class="meaning">{{Meaning}}</div>
<div class="section-title">Examples:</div>
<div class="examples">{{Example}}</div>
''',
            },
        ],
        css=css
    )

    # Create deck with name from CSV filename
    deck_name = Path(csv_path).stem
    deck = genanki.Deck(
        abs(hash(deck_name)),  # Use hash of deck name as ID
        deck_name
    )

    # Add notes
    for idx, row in df.iterrows():
        print(f"processing row {idx}")

        # Get all example columns (everything except Word and Meaning)
        example_cols = [col for col in df.columns if col.startswith('Example_')]
        
        # Get the word
        word = str(row['Word'])
        
        # Collect all non-empty examples
        examples = [str(row[col]).strip() for col in example_cols if pd.notna(row[col]) and str(row[col]).strip()]
        
        # Format examples as bullet points and make the word bold
        formatted_examples = []
        word_lower = word.lower()
        
        for example in examples:
            # Find all occurrences of the word (case insensitive)
            example_lower = example.lower()
            start = 0
            formatted_example = example
            while True:
                index = example_lower.find(word_lower, start)
                if index == -1:
                    break
                    
                # Get the actual word from original text (preserve case)
                original_word = example[index:index + len(word)]
                # Replace with bold version
                formatted_example = formatted_example.replace(original_word, f'<b>{original_word}</b>')
                start = index + 1
            
            formatted_examples.append(f'<div>• {formatted_example}</div>')
            
        formatted_examples = ''.join(formatted_examples)
        
        # Generate audio for the word
        audio_path = generate_audio(word)
        
        # Create audio tag if audio was generated
        audio_tag = ''
        if audio_path and audio_path.exists():
            try:
                # Add audio file to the deck's media files
                audio_filename = f'{word}.mp3'
                audio_tag = f'[sound:{audio_filename}]'
            except Exception as e:
                print(f"Warning: Could not process audio for word '{word}': {e}")
        
        # Color the word red if it's in special_words
        display_word = word
        if special_words and word.lower() in special_words:
            display_word = f'<span style="color: red;">{word}</span>'
        
        note = genanki.Note(
            model=model,
            fields=[display_word, str(row['Meaning']), formatted_examples, audio_tag]
        )
        deck.add_note(note)

    return deck

def process_csv_file(csv_file, anki_dir):
    """Process a single CSV file and create an Anki deck"""
    try:
        print(f"\nProcessing {csv_file}...")
        deck = convert_csv_to_anki(csv_file)
        if deck is not None:
            # Get all audio files for this deck
            temp_dir = Path('temp_audio')
            audio_files = []
            if temp_dir.exists():
                audio_files = [str(f) for f in temp_dir.glob('*.mp3')]
            
            # Create package with media files
            output_path = anki_dir / f"{csv_file.stem}.apkg"
            package = genanki.Package(deck)
            if audio_files:
                package.media_files = audio_files
            package.write_to_file(output_path)
            print(f"Created Anki deck: {output_path}")
            return True
    except pd.errors.EmptyDataError:
        print(f"Warning: {csv_file} is empty or has no valid data")
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
    return False

def main():
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Convert CSV files to Anki decks')
    parser.add_argument('path', help='Path to CSV file or directory containing CSV files')
    parser.add_argument('--special-words', '-s', help='Path to file containing special words to highlight in red')
    args = parser.parse_args()
    
    # Read special words if file provided
    special_words = read_special_words(args.special_words) if args.special_words else set()
    if special_words:
        print(f"Loaded {len(special_words)} special words")
    
    # Convert path to Path object
    input_path = Path(args.path)
    
    # Create anki_decks directory
    anki_dir = Path('anki_decks')
    anki_dir.mkdir(exist_ok=True)
    
    # Process based on whether path is file or directory
    if input_path.is_file():
        if input_path.suffix.lower() != '.csv':
            print(f"Error: {input_path} is not a CSV file")
            return
        deck = convert_csv_to_anki(input_path, special_words)
        if deck is not None:
            output_path = anki_dir / f"{input_path.stem}.apkg"
            package = genanki.Package(deck)
            package.write_to_file(output_path)
            print(f"Created Anki deck: {output_path}")
        else:
            print("Failed to process CSV file")
    
    elif input_path.is_dir():
        # Process all CSV files in directory
        csv_files = list(input_path.glob('*.csv'))
        if not csv_files:
            print(f"No CSV files found in {input_path}")
            return
        
        processed_count = 0
        for csv_file in csv_files:
            print(f"\nProcessing {csv_file}...")
            deck = convert_csv_to_anki(csv_file, special_words)
            if deck is not None:
                output_path = anki_dir / f"{csv_file.stem}.apkg"
                package = genanki.Package(deck)
                package.write_to_file(output_path)
                print(f"Created Anki deck: {output_path}")
                processed_count += 1
        
        print(f"\nProcessed {processed_count} out of {len(csv_files)} CSV files successfully")
    
    else:
        print(f"Error: {input_path} does not exist")


if __name__ == "__main__":
    main()
