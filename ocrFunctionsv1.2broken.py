#/////////////////
#// OCR FUNCTIONS
#/////////////////
# Developed by: Andrea Abellera
# Version 1.2, released April 2020
# Updates: Stem and Measure detection

import numpy as np
import math

def run(filename):
    maxpixel, array = read(filename)
    array = auto_brighten(array, maxpixel)
    sequence = [] 
    staffs = []
    staffs = detect_staff(array)
    
    print(len(staffs), "staff/s detected.\nScanning image...")
    
    for staff in staffs:
        sequence.extend(scan(array, staff))

    result = ""
    
    if len(sequence) > 0:
        
        stems = []
        for staff in staffs:
            stems.extend(stemScan(array, staff))
        
        for stem in stems:
            print(stem.print())
        
        sequence = resolveStems(sequence, stems)

        for slot in sequence:
            result += slot.print() + "\n"
    else:
        result += "No characters had been detected in the image."

    return result


def read(filename):
    maxpixel = 0
    array = np.array([0])

    try:
        imageFile = open(filename)
    except:
        print("\n\nError: Failed to open the file named \"" + filename + "\"\n\n")

    intList = []
    firstWord = True
    fileType = ""

    for line in imageFile:
        words = line.split();
        i = 0
        comment = False
        while not comment and i < len(words):
            word = words[i]
            i += 1
            if not word.startswith('#') and not firstWord:
                intList.append(int(word))
            elif word.startswith('#'):
                comment = True
            elif firstWord:
                fileType = word
                firstWord = False

    imageFile.close()

    if fileType == "P2":
        cols = intList[0] # number of columns in the image
        rows = intList[1] # number of rows in the image
        maxpixel = intList[2] # maximum pixel value
        array = np.reshape(np.array(intList[3:]), (rows, cols))
    else:
        # For the moment, only P2 files are supported
        print(fileType + " is not a recognized file type.")

    return maxpixel, array



def auto_brighten(array, maxpixel):
    max = np.amax(array)
    min = np.amin(array)

    if max != min:
        rows, cols = array.shape
        for r in range(rows):
            for c in range(cols):
                ratio_upper = max - array[r,c]
                ratio_lower = array[r,c] - min
                step = 255 / (ratio_upper + ratio_lower)
                array[r,c] = math.trunc(step * ratio_lower)
    else:
        ratio = 255 / maxpixel
        array.fill(max * ratio)

    return array



def detect_staff(array):    
    rows, cols = array.shape
    candidates = []
    staffRows = []
    staffs = []
    cut = int(cols / 7)
    for c in range(cut*3, cut*4):
        for r in range(rows):
            if array[r,c] < 160:
                candidates.append(r)

    # Get the top candidates
    top = max(candidates, key=candidates.count)
    topCount = candidates.count(top)

    for cd in candidates:
        if (topCount - candidates.count(cd) < 10) and (cd not in staffRows):
            staffRows.append(cd)

    # Condense adjacent staffs 
    r = 0
    length = len(staffRows) - 1
    while r < length:
        if  staffRows[r+1] - staffRows[r] < 3:
            staffRows.remove(staffRows[r])
            length -= 1
        else:
            r += 1

    # See if there are multiple staffs
    if len(staffRows) % 5 == 0:
        for i in range(0, len(staffRows), 5):
            staffs.append(Staff(staffRows[i:i+5]))
    else:
        print("Staff detection failed.")
    
    return staffs



def scan(array, staff):
    cols = array.shape[1]
    width = staff[3] - staff[0]
    sequence = Sequence(int(width*1.4))

    # Pre-defined test standards
    cutOff = 80     # A pixel is dark enough if below this value
    passScore = 35  # A test box is filled enough if it surpasses this value
    
    # Reduce staff to the scope of the scannable area
    staff = [key for key in staff if key >= 0 and key <= array.shape[0]]

    # Scan the staff on key areas
    for col in range(cols-width):
        newSlot = Slot(col)
        for key in range(1, len(staff)-1):
            success1 = 0
            success2 = 0
            total = 0           

            # Scan area between keys where a note may be detected
            for c in range(col, col+width):
                for r in range(staff[key-1], staff[key]):
                    total += 1

                    # Test box for fill percentage
                    if array[r,c] < cutOff:
                        success1 += 1

                for r in range(staff[key], staff[key+1]):
                    if array[r,c] < cutOff:
                        success2 += 1

            upper = success1/total * 100
            lower = success2/total * 100
            if upper >= passScore and lower >= passScore:
                fill = upper + lower / total*200
                newNote = Note(identify_char(key),fill,col)
                newSlot.append(newNote)

        if len(newSlot) > 0:
            sequence.add(newSlot)

    sequence.removeDummy()
    return sequence.toList()



def identify_char(key):
    pitches = ['D','C','B','A','G','F','E']
    char = pitches[key % 7]
    if key == 1:
        char += '++'
    elif key <= 8:
        char += '+'
    elif key >= 16:
        char += '-'
    return char
    


def stemScan(array, staff):
    stems = [Stem(0,0,0)] # dummy stem
    top = max(0,staff[0])
    bottom = min(array.shape[0],staff[len(staff)-1])
    array = array[top:bottom,:]
    rows, cols = array.shape
    
    # Scan the staff for vertical lines
    for c in range(cols):
        longest = 0
        longStart = 0
        longEnd = 0
        wasBlack = False
        start = top
        end = top

        # Determine length, start and end points of longest vertical line
        for r in range(rows):
            black = array[r,c] < 160
            if black and not wasBlack:
                start = r
                wasBlack = True
            elif not black and wasBlack:
                end = r
                wasBlack = False
                if(end - start > longest):
                    longEnd = end
                    longStart = start
                    longest = longEnd - longStart
        if wasBlack:
            end = bottom
            if(end - start > longest):
                    longStart = start
                    longEnd = end
                    longest = longEnd - longStart

        if longest >= staff.minStemLength:
            last = stems[len(stems) - 1]
            if c - last.position > 10:
                stems.append(Stem(c, longStart, longEnd))
                
    stems.remove(stems[0])  # remove dummy stem
    return stems



#If key <= 9, check right
#Else, check left
def resolveStems(sequence, stems):
    minDist = 46

    # Attach stems and identify measures
    i = 0
    for stem in stems:
        seqLength = len(sequence) - 1
        if stem.position - sequence[i].position < 0:
            print("Disjoint: " + str(stem.position) + " - " + str(sequence[i].position))
            sequence.insert(i, Measure())
        else:
            print("Attaching: " + str(stem.position) + " - " + str(sequence[i].position))
            sequence[i].attachStem()
        if i < seqLength:
            i += 1
    return sequence



class Staff(list):
    def __init__(self, positions):
        dist = int((positions[1] - positions[0]) / 2)

        # Add semi-steps beyond the staff 
        for i in range(1, 6):
            self.append(positions[0] - dist*i)   
            self.append(positions[4] + dist*i)

        # Add semi-steps between the lines
        for i in range(len(positions) - 1):
            self.append(positions[i] + dist)

        # Finally, add the detected lines
        self.extend(positions)
        self.sort()

        # Class attributes
        self.distance = dist
        self.minStemLength = dist*6
        self.measureLength = dist*8



class Note:
    def __init__(self, char, fill, position):
        self.char = char
        self.fill = fill
        self.position = position
        self.type = ""
        self.hasStem = False
        self.hasFlag = True

    def equals(self, other):
        return self.char == other.char and self.type == other.type

    def print(self):
        # Type resolution
        if self.fill >= 85:
            self.type = "quarter"
        elif self.hasStem:
            self.type = "half"
        else:
            self.type = "whole"

        return "Note: " + self.char + ", Type: " + self.type + ", Pos: " + str(self.position)



class Slot(list):
    def __init__(self, position):
        self.position = position

    def merge(self, other):
        merged = []

        # Find and keep the slot with a greater amount of notes 
        longer = self
        shorter = other
        if len(self) < len(other):     
            longer = other
            shorter = self

        for l in longer:
            for s in shorter:
                if l.equals(s):
                    l.fill = max(l.fill, s.fill)
            merged.append(l)

        self.clear() 
        self.extend(merged)

    def attachStem(self):
        for note in self:
            note.hasStem = True

    def print(self):
        notes = '['
        for note in self:
            notes += note.print()
        notes += ']'
        return notes



class Sequence:
    def __init__(self, minDist):
        self.minDist = minDist
        print(minDist)
        self.slots = [Slot(-128)] # dummy slot

    def add(self, newSlot):
        lastSlot = self.slots[len(self.slots)-1] 
        #print(str(newSlot.position) + " - " + str(lastSlot.position))
        if newSlot.position - lastSlot.position < self.minDist:
            lastSlot.merge(newSlot)
        else:
            self.slots.append(newSlot)

    def removeDummy(self):
        self.slots.remove(self.slots[0])

    def toList(self):
        return self.slots



class Stem:
    def __init__(self, position, top, bottom):
        self.position = position
        self.top = top
        self.bottom = bottom

    def print(self):
        return "Position: " + str(self.position) + ", Top: " + str(self.top) + ", Bottom: " + str(self.bottom)



class Measure:
    def print(self):
        return "|Measure|"
