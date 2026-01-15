# Speed Reading PDF Tool

A Python-based speed-reading application using **Pygame** that displays words from a PDF one at a time for rapid reading using the **Rapid Serial Visual Presentation (RSVP)** technique.

---

## Features

- Reads text directly from PDFs  
- Displays one word at a time, with the **center letter highlighted in red** for optimal focus  
- Adjustable **Words Per Minute (WPM)** using the **Up/Down arrow keys**  
- Pause and resume reading with the **Space bar**  
- Automatically logs progress to **resume later**  
- Displays:
  - Current **page number**
  - Current **WPM**
  - Current **word number**  

---

## Requirements

- Python 3.10+  
- Pygame  
- PyPDF2  

Install dependencies with:

```bash
pip install pygame PyPDF2
Usage
Place your PDF file in the same folder as the script.

Update the PDF_FILE variable in the script with your PDF’s filename.

Run the program:

bash
Copy code
python speed_reader.py
Controls:

Space bar → Pause/Resume

Up arrow → Increase WPM by 50

Down arrow → Decrease WPM by 50

The program will save your progress automatically in a log file. When reopened, it resumes a short distance before your last word for a quick refresher.