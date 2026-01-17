import os
import re
import sys
import pygame
import PyPDF2
import pytesseract
from pdf2image import convert_from_path

# ----- CONFIG -----
PDF_FILE = "Example_Quantum_Bioinformatics.pdf"
CACHE_FILE = os.path.splitext(PDF_FILE)[0] + "_cache.txt"
START_WPM = 500
WPM_STEP = 50
MIN_WPM = 20
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
FONT_SIZE = 72
INFO_FONT_SIZE = 24
BACKGROUND_COLOR = (0, 0, 0)
LETTER_COLOR = (255, 255, 255)
CENTER_COLOR = (255, 0, 0)
REFRESH_BACKWORDS = 100

POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# ------------------

# ----- LOAD CACHE FILE -----
start_index = 0
current_wpm = START_WPM
pages_text = []

if os.path.exists(CACHE_FILE):
    print("Loading from cache file...")
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        # First line = WPM
        try:
            current_wpm = int(lines[0].strip())
        except:
            current_wpm = START_WPM
        # Second line = last word index
        try:
            start_index = max(int(lines[1].strip()) - REFRESH_BACKWORDS, 0)
        except:
            start_index = 0
        # Remaining lines = processed text
        pages_text = "".join(lines[2:]).split("\n\n---PAGE---\n\n")

# ----- PROCESS PDF IF CACHE EMPTY -----
if not pages_text or all(not p.strip() for p in pages_text):
    print("Processing PDF...")
    pages_text = []
    with open(PDF_FILE, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    # If PDF has no text, use OCR
    if len(pages_text) == 0:
        print("No text found, using OCR...")
        images = convert_from_path(PDF_FILE, dpi=300, poppler_path=POPPLER_PATH)
        for img in images:
            gray = img.convert('L')
            pages_text.append(pytesseract.image_to_string(gray))

    # Save processed text + WPM/index to cache
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(f"{current_wpm}\n{start_index}\n")
        for page in pages_text:
            f.write(page.strip() + "\n\n---PAGE---\n\n")

# ----- EXTRACT WORDS -----
words_info = []
for page_idx, page in enumerate(pages_text):
    for word in re.findall(r'\b\w+\b', page):
        words_info.append((word, page_idx + 1))

total_words = len(words_info)
print(f"Total words extracted: {total_words}")

# ----- INITIALIZE PYGAME -----
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Speed Reading")
font = pygame.font.SysFont(None, FONT_SIZE)
info_font = pygame.font.SysFont(None, INFO_FONT_SIZE)
clock = pygame.time.Clock()

def draw_word(word, page, wpm, word_index):
    screen.fill(BACKGROUND_COLOR)
    word_cap = word.capitalize()
    length = len(word_cap)
    center_idx = length // 2

    letter_surfaces = []
    for i, letter in enumerate(word_cap):
        color = CENTER_COLOR if i == center_idx else LETTER_COLOR
        surf = font.render(letter, True, color)
        letter_surfaces.append(surf)

    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2
    left_width = sum(surf.get_width() for surf in letter_surfaces[:center_idx])
    center_width = letter_surfaces[center_idx].get_width()
    x = center_x - center_width // 2 - left_width

    for surf in letter_surfaces:
        screen.blit(surf, (x, center_y - surf.get_height() // 2))
        x += surf.get_width()

    # Draw WPM in bottom right
    wpm_surf = info_font.render(f"WPM: {wpm}", True, (255, 255, 0))
    screen.blit(wpm_surf, (SCREEN_WIDTH - wpm_surf.get_width() - 10, SCREEN_HEIGHT - wpm_surf.get_height() - 10))

    # Draw Page number in bottom left
    page_surf = info_font.render(f"Page: {page}", True, (255, 255, 0))
    screen.blit(page_surf, (10, SCREEN_HEIGHT - page_surf.get_height() - 10))

    # Draw current word number in bottom center
    index_surf = info_font.render(f"Word: {word_index+1}", True, (0, 255, 255))
    screen.blit(index_surf, (SCREEN_WIDTH // 2 - index_surf.get_width() // 2, SCREEN_HEIGHT - index_surf.get_height() - 10))

    pygame.display.flip()

def wpm_to_duration(wpm):
    return max(60000 / wpm, 10)

# ----- MAIN LOOP -----
paused = False
i = start_index
current_duration = wpm_to_duration(current_wpm)

try:
    while i < total_words:
        word, page = words_info[i]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Save WPM, index, and keep processed text
                with open(CACHE_FILE, "r+", encoding="utf-8") as f:
                    lines = f.readlines()
                    lines[0] = f"{current_wpm}\n"
                    lines[1] = f"{i}\n"
                    f.seek(0)
                    f.writelines(lines)
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                    if paused:
                        with open(CACHE_FILE, "r+", encoding="utf-8") as f:
                            lines = f.readlines()
                            lines[0] = f"{current_wpm}\n"
                            lines[1] = f"{i}\n"
                            f.seek(0)
                            f.writelines(lines)
                        print(f"Paused at word {i}")
                elif event.key == pygame.K_UP:
                    current_wpm += WPM_STEP
                    current_duration = wpm_to_duration(current_wpm)
                    print(f"Speed increased: {current_wpm} WPM")
                elif event.key == pygame.K_DOWN:
                    current_wpm = max(MIN_WPM, current_wpm - WPM_STEP)
                    current_duration = wpm_to_duration(current_wpm)
                    print(f"Speed decreased: {current_wpm} WPM")

        if not paused:
            draw_word(word, page, current_wpm, i)
            i += 1
            pygame.time.wait(int(current_duration))
        else:
            clock.tick(30)

except KeyboardInterrupt:
    print("\nInterrupted by user!")

finally:
    # Save final WPM, index, and keep processed text
    with open(CACHE_FILE, "r+", encoding="utf-8") as f:
        lines = f.readlines()
        lines[0] = f"{current_wpm}\n"
        lines[1] = f"{i}\n"
        f.seek(0)
        f.writelines(lines)
    pygame.quit()
    sys.exit()
