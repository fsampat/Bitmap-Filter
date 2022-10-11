import os.path
import PySimpleGUI as sg

# define window values
WINDOWX = 650
WINDOWY = 125
BUTTONX = 15
BUTTONY = 1
DESCRIPTION ="To apply filter, first select a 24 bit uncompressed bitmap file and then click the desired filter option.\nThe filtered file will appear in the same directory upon completion."

# checks user provided file path to ensure it is a bitmap
def checkFile(values):

    #check if file supplied exists
    if not values["imagepath"]:
        sg.Popup('Please select a .BMP file to filter.', keep_on_top=True)
        return False   
    elif os.path.isfile(values["imagepath"]) == False:
        sg.Popup('File not found.', keep_on_top=True)
        return 
    elif ".bmp" in values["imagepath"]:
        return True  
    
    sg.Popup('Unsupported file type.', keep_on_top=True)
    return False

def filter(values, event):

    iname = values["imagepath"]

    # open file provided by user and create new output file to store desired filter effect
    with open(iname, "rb") as input_file:
               
        # store header info.  Need to check headers to confirm valid bitmap file!
        BITMAPFILEHEADER = input_file.read(14)
        BITMAPINFOHEADER = input_file.read(40)

        # get key header info for validation and conversion.  all integer values in a bitmap file are stored in little endian format

        fileheader = BITMAPFILEHEADER[0:2].hex()
        offset = int.from_bytes(BITMAPFILEHEADER[10:14], "little", signed=True)

        width = int.from_bytes(BITMAPINFOHEADER[4:8], "little", signed=True)
        height = abs(int.from_bytes(BITMAPINFOHEADER[8:12], "little", signed=True))
        bits_per_pixel = int.from_bytes(BITMAPINFOHEADER[14:16], "little", signed=False)
        compression = int.from_bytes(BITMAPINFOHEADER[16:20], "little", signed=False)
        infoheadersize =  int.from_bytes(BITMAPINFOHEADER[0:4], "little", signed=False)

        #check if bitmap file supplied, with good certainty, is a 24 bit uncompressed BMP 4.0 file
        if fileheader != "424d" and offset != 54 and infoheadersize != 40 and bits_per_pixel != 24 and compression !=0:
            sg.Popup('Unsupported file type.', keep_on_top=True)
            return

        bytes_per_pixel = int(bits_per_pixel / 8)

        # determine padding, if required, for each line to ensure divisible by 4
        width_in_bytes = int(width * bits_per_pixel / 8)
        padding = width_in_bytes % 4

        # store bitmap imagage into 2D list of dictionaries. discard padding.
        image = []
        for y in range(height):
            # for each line, store pixel (3 bytes) dictionary into a list
            row = []
            for x in range(width):
                pixel = {}
                pixel_input = input_file.read(bytes_per_pixel)
                pixel["Blue"] = pixel_input[0:1]
                pixel["Green"] = pixel_input[1:2]
                pixel["Red"] = pixel_input[2:3]
                row.append(pixel)

            image.append(row)
            input_file.read(padding)

    # check user input for conversion type and label output file appropriately
    if(event == "Blur"):
        filtered_image = blur(image, height, width)
        oname = iname + "_blur.bmp"
    elif(event == "Grayscale"):
        filtered_image = grayscale(image, height, width)
        oname = iname + "_grayscale.bmp"
    elif(event == "Reflection"):
        filtered_image = reflection(image, height, width)
        oname = iname + "_reflection.bmp"
    elif(event == "Sepia"):
        filtered_image = sepia(image, height, width)
        oname = iname + "_sepia.bmp"
    elif(event == "Sobel"):
        filtered_image = sobel(image, height, width)
        oname = iname + "_sobel.bmp"

    # write filtered image to output file
    with open(oname, "wb") as output_file:
        output_file.write(BITMAPFILEHEADER)
        output_file.write(BITMAPINFOHEADER)

        for y in range(height):
            for x in range(width):
                output_file.write(filtered_image[y][x]["Blue"])
                output_file.write(filtered_image[y][x]["Green"])
                output_file.write(filtered_image[y][x]["Red"])
            
            # add padding
            for x in range(padding):
              output_file.write(b'\0') 

    sg.Popup('Successfully converted. Check folder.', keep_on_top=True)
                

def blur(image, height, width):
    
    blurred_image = []

    for y in range(height):
        row = []
        for x in range(width):
            pixel = {}
            blue = 0
            green = 0
            red = 0
            count = 0

            # use box blur method to create desired effect
            for i in range(10):
                if y - 1 + i < 0 or y - 1 + i > height - 1:
                    continue

                for j in range(10):
                    if x - 1 + j >= 0 and x - 1 + j < width - 1:
                        count += 1
                        blue += image[y - 1 + i][x - 1 + j]["Blue"][0]
                        green += image[y - 1 + i][x - 1 + j]["Green"][0]
                        red += image[y - 1 + i][x - 1 + j]["Red"][0]

            pixel["Blue"] = round(blue/count).to_bytes(1, "little", signed=False)
            pixel["Green"] = round(green/count).to_bytes(1, "little", signed=False)
            pixel["Red"] = round(red/count).to_bytes(1, "little", signed=False)
            row.append(pixel)

        blurred_image.append(row)

    return blurred_image


def grayscale(image, height, width):

    for y in range(height):
        for x in range(width):
            # calculate average RGB value for each pixel to give grayscale effect
            green = image[y][x]["Green"][0]
            blue = image[y][x]["Blue"][0]
            red = image[y][x]["Red"][0]
            average = round(((red + green + blue)/3))

            image[y][x]["Green"] = average.to_bytes(1, "little", signed=False)
            image[y][x]["Blue"] = average.to_bytes(1, "little", signed=False)
            image[y][x]["Red"] = average.to_bytes(1, "little", signed=False)
    return image


def reflection(image, height, width):

    for y in range(height):
        for x in range(int(width/2)):
            # reflect image horizontally
            temp = image[y][width - 1 - x] 
            image[y][width - 1 - x] = image[y][x]
            image[y][x] = temp

    return image
    

def sepia(image, height, width):
    
    for y in range(height):
        for x in range(width):

            blue = image[y][x]["Blue"][0]
            green = image[y][x]["Green"][0]
            red = image[y][x]["Red"][0]

            # cap sepia values at 255
            sepiaBlue = round(.272 * red + .534 * green + .131 * blue)
            if sepiaBlue > 255:
                sepiaBlue = 255
            sepiaGreen = round(.349 * red + .686 * green + .168 * blue)
            if sepiaGreen > 255:
                sepiaGreen = 255
            sepiaRed = round(.393 * red + .769 * green + .189 * blue)
            if sepiaRed > 255:
                sepiaRed = 255

            image[y][x]["Blue"] = sepiaBlue.to_bytes(1, "little", signed=False)
            image[y][x]["Green"] = sepiaGreen.to_bytes(1, "little", signed=False)
            image[y][x]["Red"] = sepiaRed.to_bytes(1, "little", signed=False)
    return image


def sobel(image, height, width):
   
    blurred_image = []

    for y in range(height):
        row = []
        
        for x in range(width):
            pixel = {}
            bluex = 0
            bluey = 0
            blue = 0
            greenx = 0
            greeny = 0
            green = 0
            redx = 0
            redy = 0
            red = 0
            count = 0

            # populate Sobel Matrices to support conversion
            Gx = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
            Gy = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]

            # use Sobel Filter Algorithm to create desired effect
            for i in range(3):
                if y - 1 + i < 0 or y - 1 + i > height - 1:
                    continue

                for j in range(3):
                    if x - 1 + j >= 0 and x - 1 + j < width - 1:
                        count += 1
                        bluex += image[y - 1 + i][x - 1 + j]["Blue"][0]*Gx[i][j]
                        bluey += image[y - 1 + i][x - 1 + j]["Blue"][0]*Gy[i][j]
                        greenx += image[y - 1 + i][x - 1 + j]["Green"][0]*Gx[i][j]
                        greeny += image[y - 1 + i][x - 1 + j]["Green"][0]*Gy[i][j]
                        redx += image[y - 1 + i][x - 1 + j]["Red"][0]*Gx[i][j]
                        redy += image[y - 1 + i][x - 1 + j]["Red"][0]*Gy[i][j]

            # cap RGB at 255 if overflow
            blue = round((bluex**2 + bluey**2)**.5)
            if blue > 255:
                blue = 255

            green = round((greenx**2 + greeny**2)**.5)
            if green > 255:
                green = 255

            red = round((redx**2 + redy**2)**.5)
            if red > 255:
                red = 255
            
            # convert RGB ints to bytes
            pixel["Blue"] = blue.to_bytes(1, "little", signed=False)
            pixel["Green"] = green.to_bytes(1, "little", signed=False)
            pixel["Red"] = red.to_bytes(1, "little", signed=False)
            row.append(pixel)

        blurred_image.append(row)

    return blurred_image


def main():

    # define window look and feel
    sg.theme('SystemDefaultForReal')
    sg.FileBrowse()
    ttk_style = 'vista'
    layout = [[sg.T(DESCRIPTION)],
            [sg.Text("Choose a file:"), sg.Input(), sg.FileBrowse(key="imagepath")],
            [sg.Button("Grayscale", use_ttk_buttons=True, size=(BUTTONX,BUTTONY)), sg.Button("Reflection", use_ttk_buttons=True, size=(BUTTONX,BUTTONY)), sg.Button("Blur", use_ttk_buttons=True, size=(BUTTONX,BUTTONY)), sg.Button("Sepia", use_ttk_buttons=True, size=(BUTTONX,BUTTONY)), sg.Button("Sobel", use_ttk_buttons=True, size=(BUTTONX,BUTTONY))]] 
            
    # build window
    window = sg.Window('Bitmap Image Filter developed by Sampat Technologies Inc.', layout, ttk_theme=ttk_style, size=(WINDOWX,WINDOWY))

    # listen for an event from user and then take appropriate action
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif checkFile(values):
            filter(values, event)

main()

