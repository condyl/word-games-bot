def filter_collins_wordlist():
    input_file = 'word_lists/collins-word-list-2019.txt'
    output_file = 'word_lists/collins-word-list-2019-filtered.txt'
    
    try:
        # Read all words from the file
        with open(input_file, 'r', encoding='utf-8') as f:
            words = f.read().splitlines()
        
        # Filter out 2-letter words and words longer than 16 letters
        filtered_words = [word for word in words if 2 < len(word) <= 16]
        
        # Save filtered words back to new file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(filtered_words))
            
        # Calculate statistics
        removed_short = len([w for w in words if len(w) == 2])
        removed_long = len([w for w in words if len(w) > 16])
        
        print(f"Original word count: {len(words)}")
        print(f"Words removed (2 letters): {removed_short}")
        print(f"Words removed (>16 letters): {removed_long}")
        print(f"Total words removed: {len(words) - len(filtered_words)}")
        print(f"New word count: {len(filtered_words)}")
        print(f"Filtered wordlist saved to: {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Could not find input file: {input_file}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    filter_collins_wordlist() 