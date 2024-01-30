
#!/usr/bin/env python3
import argparse
import pytesseract
from PIL import Image
import argcomplete
import re
import logging

# Configure logging
logging.basicConfig(filename='ocr_word_finder.log', filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_image(image_path):
    try:
        logging.info(f"Opening image: {image_path}")
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        logging.info("Text extraction successful.")
        return text
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return None

def search_keywords_in_text(text, keywords):
    results = {}
    for keyword in keywords:
        pattern = re.compile(r'([^.]*?'+re.escape(keyword)+r'[^.]*\.)', re.IGNORECASE)
        matches = pattern.findall(text)
        results[keyword] = matches
        logging.info(f"Keyword '{keyword}' found {len(matches)} times in the text.")
        for match in matches:
            logging.info(f" - Found in sentence: '{match.strip()}'")
    return results

def main(image_path, keywords):
    logging.info("Script started.")
    text = extract_text_from_image(image_path)
    if text:
        results = search_keywords_in_text(text, keywords)
        for keyword, matches in results.items():
            print(f"Keyword '{keyword}' found {len(matches)} times.")
    else:
        print("No text extracted from the image.")
    logging.info("Script finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for keywords in text extracted from an image.")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("keywords", nargs='+', help="Keywords to search for (multiple keywords allowed)")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    main(args.image_path, args.keywords)

