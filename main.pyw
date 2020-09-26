#///////////////////
#// MUSIC SHEET OCR
#///////////////////
# Developed by: Andrea Abellera
# Version 1.2, released May 2020
# Updates: Added Tkinter interface; Rewrote code to integrate with GUI


import tkinter as tk
import ocrFunctions as ocr
import numpy as np


# Set-up GUI window
window = tk.Tk()
window.title("Sheet Music OCR")
window.geometry("300x400")

sheetInfo = []  # Will contain 4 elements if import is successful:
                # 1. Image matrix
                # 2. Maximum pixel value
                # 3. Number of rows
                # 4. Number of columns

sheetDisplay = tk.PhotoImage(width=0, height=0)

def plot_point(x, y):
    sheetDisplay.put("{red}", (x, y))


def import_sheet(event):
    filename = file_txt.get()
    
    validate = True
    # Validate file, if does not exist, show messagebox and don't run    

    if validate:
        sheetInfo = []
        for info in ocr.import_sheet(filename):
            sheetInfo.append(info)
        array, maxpixel, rows, cols = sheetInfo
        sheetDisplay.configure(width=cols, height=rows)
        #display_lbl.image = sheetDisplay
        #display_lbl.configure(image = sheetDisplay)
        for r in range(rows):
            for c in range(cols):
                plot_point(r,c)
        display_lbl.image = sheetDisplay
        display_lbl.configure(image = sheetDisplay)        
        result_lbl.configure(text=maxpixel)


def run_OCR(event):
    ocrResult = ocr.run(sheetInfo[0], sheetInfo[1])
    result_lbl.configure(text=ocrResult)


# Set-up widgets
instr_lbl = tk.Label(window, text="Please provide a file name in the form image.pgm", font=("Arial", 10))
file_txt = tk.Entry(window, width=30)
import_btn = tk.Button(window, text="Import", font=("Arial", 10))
import_btn.bind("<Button-1>", import_sheet)
display_lbl = tk.Label(window, text="Sheet will be displayed here")
run_btn = tk.Button(window, text="Run OCR", font=("Arial", 10))
run_btn.bind("<Button-1>", run_OCR)
result_lbl = tk.Label(window, text="Results will be displayed here", font=("Arial", 10))

# Pack widgets
instr_lbl.pack()
file_txt.pack()
import_btn.pack()
display_lbl.pack()
run_btn.pack()
result_lbl.pack()

window.mainloop()