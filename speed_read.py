import pygame
import sys
import re
import PyPDF2
import os
import pytesseract
from pdf2image import convert_from_path

# ----- CONFIG -----
PDF_FILE = "Example_Quantum_Bioinformatics.pdf"
CONFIG_FILE = "speed_read_config.txt"
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
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"C:\poppler-25.12.0\Library\bin"
# ------------------

# ----- LOAD PDF TEXT -----
pages_text = []
with open(PDF_FILE, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages_text.append(page_text)

# If no text found, use OCR
if len(pages_text) == 0:
    print("No text found in PDF, using OCR...")
    images = convert_from_path(PDF_FILE, dpi=300, poppler_path=poppler_path)
    for img in images:
        # Convert image to grayscale for better OCR accuracy
        gray = img.convert('L')
        # Optional: thresholding can help for poor scans
        # gray = gray.point(lambda x: 0 if x < 128 else 255, '1')
        text = pytesseract.image_to_string(gray)
        pages_text.append(text)

# ----- PROCESS WORDS AND TRACK PAGES -----
words_info = []  # list of (word, page_num)
for page_idx, page in enumerate(pages_text):
    for word in re.findall(r'\b\w+\b', page):
        words_info.append((word, page_idx + 1))

total_words = len(words_info)

# ----- LOAD LOG -----
log_file = f"{os.path.splitext(PDF_FILE)[0]}_log.txt"
config_file = f"{os.path.splitext(PDF_FILE)[0]}_config.txt"
start_index = 0
if os.path.exists(log_file):
    with open(log_file, "r") as f:
        try:
            saved_index = int(f.read())
            start_index = max(saved_index - REFRESH_BACKWORDS, 0)
            print(f"Resuming at word {start_index}")
        except:
            pass

# ----- INITIALIZE PYGAME -----
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Speed Reading")
font = pygame.font.SysFont(None, FONT_SIZE)
info_font = pygame.font.SysFont(None, INFO_FONT_SIZE)

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

def save_config():
    with open(CONFIG_FILE, "w") as f:
        f.write(f"WPM: {current_wpm}\n")


# ----- MAIN LOOP SETUP -----
paused = False
i = start_index
clock = pygame.time.Clock()
current_wpm = START_WPM
current_duration = wpm_to_duration(current_wpm)

current_wpm = START_WPM
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            line = f.readline()
            if line.startswith("WPM:"):
                current_wpm = int(line.strip().split(":")[1])
                print(f"Resuming with WPM: {current_wpm}")
    except:
        pass

# ----- MAIN LOOP -----

try:
    while i < total_words:
        word, page = words_info[i]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                with open(log_file, "w") as f:
                    f.write(str(i))
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                    if paused:
                        with open(log_file, "w") as f:
                            f.write(str(i))
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
    # Always save log and config
    with open(log_file, "w") as f:
        f.write(str(i))
    save_config()
    pygame.quit()
    sys.exit()