from libs.functions import indent
from libs.waveshare_epd import epd3in7
from PIL import Image,ImageDraw,ImageFont 
from time import sleep
from gpiozero import Button              
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
from os import path
from glob import glob
from math import ceil
from textwrap import wrap
import board
from adafruit_neokey.neokey1x4 import NeoKey1x4
i2c_bus = board.I2C()
neokey = NeoKey1x4(i2c_bus, addr=0x30)


btn1 = neokey[0]
btn2 = neokey[1]
btn3 = neokey[2]
btn4 = neokey[3]
#btn1 = Button(5)
#btn2 = Button(6)
#btn3 = Button(13)
#btn4 = Button(19) 
fonts_dir='fonts/'
BOOKFONT = fonts_dir + 'DejaVuSansMono.ttf'
LARGEFONT = fonts_dir + 'Lobster-Regular.ttf'
fontBook = ImageFont.truetype(BOOKFONT,16)
fontLg = ImageFont.truetype(LARGEFONT,50)
fontMenu = ImageFont.truetype(BOOKFONT,10)
fontBookTitle = ImageFont.truetype(BOOKFONT,17)
refreshCount = 0
pageNum = 0
bookNum = 0
bookLen = 0
mechButton = 0
lightState = [False,False,False,False]
books_dir='books/'
cache_dir='cache/'
bookNameList = []
fullBook = []
bookListFull = sorted(glob(books_dir + "*.epub"))
for i in bookListFull:
    x = i.split('/')
    bookNameList.append(x[-1])
bookTitleList = []
for i in bookNameList:
    bookTitleList.append(epub.read_epub(books_dir+i).get_metadata('DC','title')[0][0])
epd = epd3in7.EPD() # 480x280
h = epd.height
w = epd.width
GRAY4 = epd.GRAY4
epd.init(0)              # initialize the display
epd.Clear(0xff,0)             # clear the display


def getCharScrSz(font,font2):
    global screenWidthChar
    global screenWidthCharBT
    global screenHeightChar
    global screenHeightCharBT
    global lineHeight
    global lineHeightBT
    charStr=''
    while font.getsize(charStr)[0] < (w-6):
        charStr += 'a'
    screenWidthChar = len(charStr)
    screenHeightChar = round((h-30) / font.getsize(charStr)[1])
    lineHeight = font.getsize(charStr)[1]
    charStr=''
    while font2.getsize(charStr)[0] < (w-20):
        charStr += 'a'
    screenWidthCharBT = len(charStr)
    screenHeightCharBT = round((h-30) / font2.getsize(charStr)[1])
    lineHeightBT = font2.getsize(charStr)[1]

def checkLastRead():
    global book
    global bookNum
    if path.exists(cache_dir + 'last-read.cache'):
        f = open(cache_dir + 'last-read.cache')
        book = f.read()
        bookNum = bookNameList.index(book)
        f.close()
    else:
        book = bookNameList[bookNum]

def checkLastPage():
    global pageNum
    global bookLen
    if path.exists(cache_dir + book.split('.')[0] + '.cache'):
        f = open(cache_dir + book.split('.')[0] + '.cache')
        pageNumStr = f.read()
        pageNum = int(pageNumStr)
        bookLen = ceil(len(fullBook) / screenHeightChar)
        f.close()
    else:
        pageNum = 0
        bookLen = ceil(len(fullBook) / screenHeightChar)
 
def pageNumCache():
    bookLen = ceil(len(fullBook) / screenHeightChar)
    bookFileName=book.split('.')
    f = open(cache_dir + bookFileName[0]+'.cache','w')
    f.write(str(pageNum))
    f.close()

def lastReadCache():
    f = open(cache_dir + 'last-read.cache','w')
    f.write(book)
    f.close

def printToDisplay(string):
    HBlackImage = Image.new('1', (w, h), 0xff)  # 480x280
    draw = ImageDraw.Draw(HBlackImage)
    draw.text((indent(string,fontLg,w), 2), string, font = fontLg, fill = GRAY4)
    #bookVar = epub.read_epub(books_dir + book)
    #bookTitle = epub.read_epub(books_dir+book).get_metadata('DC','title')[0][0]
    bookTitle = bookTitleList[bookNum]
    bookTitleWrap = wrap(bookTitle,width=screenWidthCharBT)
    x = 1
    for i in bookTitleWrap:
        draw.text((indent(i,fontBookTitle,w),70+x*lineHeightBT),i,font=fontBookTitle,fill=GRAY4)
        x+=1
    #printMenuInterface(draw)
    screenCleanup()
    epd.display_4Gray(epd.getbuffer_4Gray(HBlackImage))

def printToSplash(string):
    HBlackImage = Image.new('1', (w, h), 0xff)  # 480x280 
    draw = ImageDraw.Draw(HBlackImage)
    draw.text((indent(string,fontLg,w), 90), string, font = fontLg, fill = GRAY4)
    screenCleanup()
    epd.display_4Gray(epd.getbuffer_4Gray(HBlackImage))

def printInterface(draw):
    draw.line((0,250,174,250),fill=GRAY4,width=1)
    draw.line((43,250,43,264),fill=GRAY4,width=1)
    draw.line((87,250,87,264),fill=GRAY4,width=1)
    draw.line((130,250,130,264),fill=GRAY4,width=1)
    draw.text((indent('Menu',fontMenu,w/4),250),'Menu',font=fontMenu,fill=GRAY4)
    draw.text((indent('Prev',fontMenu,w/4)+43,250),'Prev',font=fontMenu,fill=GRAY4)
    draw.text((indent('Next',fontMenu,w/4)+87,250),'Next',font=fontMenu,fill=GRAY4)
    draw.text((indent('Back',fontMenu,w/4)+130,250),'Back',font=fontMenu,fill=GRAY4)
    draw.text((indent(str(pageNum),fontMenu,w)+80, 235), str(pageNum), font = fontMenu, fill = GRAY4)

def printMenuInterface(draw):
    draw.line((0,250,174,250),fill=GRAY4,width=1)
    draw.line((43,250,43,264),fill=GRAY4,width=1)
    draw.line((87,250,87,264),fill=GRAY4,width=1)
    draw.line((130,250,130,264),fill=GRAY4,width=1)
    draw.text((indent('Sel.',fontMenu,w/4),250),'Sel.',font=fontMenu,fill=GRAY4)
    draw.text((indent('Prev',fontMenu,w/4)+43,250),'Prev',font=fontMenu,fill=GRAY4)
    draw.text((indent('Next',fontMenu,w/4)+87,250),'Next',font=fontMenu,fill=GRAY4)
    draw.text((indent('Quit',fontMenu,w/4)+130,250),'Quit',font=fontMenu,fill=GRAY4)

def loadBook(bookPath):
    global fullBook
    fullBook = []
    bookRead = epub.read_epub(bookPath)
    for chapter in bookRead.get_items_of_type(ebooklib.ITEM_DOCUMENT): # loop all chapters in book
        soup = BeautifulSoup(chapter.get_body_content(),'html5lib')
        chapterString = soup.get_text()
        chapterString = chapterString.replace("\t","").replace("\r","").replace("    "," ")##.replace("\n","")
        chapterText = wrap(chapterString,width=screenWidthChar)
        for x in chapterText: # append chapter to fullBook
            fullBook.append(x)

def printPage(pageNum):
    HBlackImage = Image.new('1', (w, h), 0xff)  # 480x280
    draw = ImageDraw.Draw(HBlackImage)
    for i in range(screenHeightChar):
        listIndex = (pageNum * screenHeightChar) + i
        if listIndex < len(fullBook):
            draw.text((1,i*lineHeight),fullBook[listIndex],font=fontBook,fill=GRAY4)
    #printInterface(draw)
    screenCleanup()
    epd.display_4Gray(epd.getbuffer_4Gray(HBlackImage))
    pageNumCache()
    lastReadCache()

def screenCleanup():
    global refreshCount
    refreshCount +=1
    if refreshCount == 10:
        epd.init(0)
        epd.Clear(0xff,0)
        refreshCount = 0

#def screenCleanup():
#    epd.init(0)
#    epd.Clear(0xff,0)


def nextPage():
    global pageNum
    pageNum +=1

def prevPage():
    global pageNum
    if pageNum > 0:
        pageNum -=1

def nextBook():
    global book
    global bookNum
    if bookNum < (len(bookNameList)-1): 
        bookNum +=1
    book = bookNameList[bookNum]

def prevBook():
    global book
    global bookNum
    if bookNum > 0:
        bookNum -=1
    book = bookNameList[bookNum]
   
def sideLight():
    if lightState[1]:
        neokey.pixels[1] = 0x0
        lightState[1] = False
    else:
        neokey.pixels[1] = 0xFFFF00
        lightState[1] = True
 
def handleBtnPress(btn):
    if btn.pin.number == 5:
        printPage(pageNum)
    if btn.pin.number == 6:
        prevPage()
        printPage(pageNum)
    if btn.pin.number == 13:
        nextPage()
        printPage(pageNum) 
    if btn.pin.number == 19:
        printToDisplay('Welcome!')

def handleBtnPress2(btn):
    if btn == 0:
        printPage(pageNum)
        sideLight()
    if btn == 1:
        prevPage()
        printPage(pageNum)
    if btn == 2:
        nextPage()
        printPage(pageNum)
    if btn == 3:
        printToDisplay('Welcome!')

def handleMenuBtn(btn):
    if btn.pin.number == 6:
        prevBook()
        printToDisplay('Welcome!')
    if btn.pin.number == 13:
        nextBook()
        printToDisplay('Welcome!')
    if btn.pin.number == 19:
        printToSplash('Goodbye')

def handleMenuBtn2(btn):
    if btn == 1:
        prevBook()
        printToDisplay('Welcome!')
    if btn == 2:
        nextBook()
        printToDisplay('Welcome!')
    if btn == 3:
        printToSplash('Goodbye')



def menuLoop():
    global books_dir
    global book
    global bookNum
    global mechButton
    while True:
        #if btn1.is_pressed:
        if neokey[0]:
            printToSplash('Loading')
            checkLastPage()
            loadBook(books_dir + book)
            pageTurnLoop()
        #btn2.when_pressed = handleMenuBtn
        if neokey[1]:
            mechButton = 1
            handleMenuBtn2(mechButton)
        #btn3.when_pressed = handleMenuBtn
        if neokey[2]:
            mechButton = 2
            handleMenuBtn2(mechButton)
        #if btn4.is_pressed:
        if neokey[3]:
            #btn4.when_pressed = handleMenuBtn
            mechButton = 3
            handleMenuBtn2(mechButton)
            sleep(6)
            raise Exception("Quit")

def pageTurnLoop():
    global mechButton
    printPage(pageNum)
    while True:
        if neokey[0]:
            sideLight()
            sleep(1)
        #btn2.when_pressed = handleBtnPress
        if neokey[1]:
            mechButton = 1
            handleBtnPress2(mechButton)
        #btn3.when_pressed = handleBtnPress
        if neokey[2]:
            mechButton = 2
            handleBtnPress2(mechButton)
        #if btn4.is_pressed:
        if neokey[3]:
            #btn4.when_pressed = handleBtnPress
            mechButton = 3
            handleBtnPress2(mechButton)
            sleep(1.5)
            break

try:
    getCharScrSz(fontBook,fontBookTitle)
    checkLastRead()
    printToDisplay('Welcome!')
    menuLoop()

except IOError as e:
    epd.sleep()
    print(e)

