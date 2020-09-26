#///////////////////
#// SHEET MUSIC OCR
#///////////////////
# Developed by: Andrea Abellera


import sys
import ocrFunctions as ocr

def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        ocrResult = ocr.run(filename)
        print(ocrResult)
    else:
        print("Please provide a file name in the form image.pgm.")
        return



if __name__ == "__main__":
    main()   