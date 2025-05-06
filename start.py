import ST7735
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from getaqdata import connect_and_read


def render(rgbImage):
  #R,G,B = rgbImage.split()
  #display_image(Image.merge('RGB', (B, G, R)))
  ST7735.display_image(rgbImage)

def textsize(text, font):
    im = Image.new(mode="P", size=(0, 0))
    draw = ImageDraw.Draw(im)
    _, _, width, height = draw.textbbox((0, 0), text=text, font=font)
    return width, height

def createBlankImage(width, height, color):
  image = Image.new("RGB", (width, height), color)
  
  draw = ImageDraw.Draw(image)
  return image, draw

def drawHorizontalRule(image, draw, top, padding, thick, fill):
  draw.line([(padding, top), (image.width-padding, top)], fill =fill, width = thick)

def drawTextAtPos(draw, font, left, top, text, color):
  draw.text((left, top), text, font=font, fill=color)
  textWidth, textHeight = textsize(text, font=font)
  return left, top, textWidth, textHeight

def drawTextLeft(draw, font, top, padding, rowwidth, text, color):
  #w, h = draw.textsize(text, font=font)
  return drawTextAtPos(draw=draw, font=font, left=padding, top=top, text=text, color=color)

def drawTextRight(draw, font, top, padding, rowwidth, text, color):
  textWidth, textHeight = textsize(text, font=font)
  return drawTextAtPos(draw=draw, font=font, left=int(rowwidth - padding - textWidth), top=top, text=text, color=color)

def drawTextCenter(draw, font, top, padding, rowwidth, text, color):
  textWidth, textHeight = textsize(text, font=font)
  return drawTextAtPos(draw=draw, font=font, left=int(rowwidth/2 - textWidth/2), top=top, text=text, color=color)

def drawImageAtPos(targetImage, imageToDraw, left, top):
    
  targetImage.paste(imageToDraw, (left, top))
  return left, top, imageToDraw.width, imageToDraw.height

def drawImageLeft(targetImage, top, padding, rowwidth, imageToDraw):
  return drawImageAtPos(targetImage=targetImage, imageToDraw=imageToDraw, left=padding, top=top)

def drawImageRight(targetImage, top, padding, rowwidth, imageToDraw):
  return drawImageAtPos(targetImage=targetImage, imageToDraw=imageToDraw, left=int(rowwidth - padding - imageToDraw.width), top=top)

def drawImageCenter(targetImage, top, padding, rowwidth, imageToDraw):
  return drawImageAtPos(targetImage=targetImage, imageToDraw=imageToDraw, left=int(rowwidth/2 - imageToDraw.width/2), top=top)

def get_aq_value_index_color(index: int):
  if index < 20:
      return '#1DCFFF'
  elif index < 50:
      return '#43D357'
  elif index < 100:
      return '#FDB80D'
  elif index < 150:
      return '#E9365A'
  elif index < 250:
      return '#A829D4'
  else:
      return '#6A0AFF'
        
def get_aq_value_index_icon(index: int):
  if index < 20:
      return 'good.bmp'
  elif index < 50:
      return 'fair.bmp'
  elif index < 100:
      return 'moderate.bmp'
  elif index < 150:
      return 'poor.bmp'
  elif index < 250:
      return 'very-poor.bmp'
  else:
      return 'poisonous.bmp'  

def getPageOne(fybra_device_values: list[str] | None, aq_values: list[list[str]] | None):
  screenWidth = 128
  screenHeight = 160
  
  leftRightPadding = 3
  
  isDarkTheme = None
  
  now = datetime.now()
  if(now.hour > 6 and now.hour < 21):
      isDarkTheme = False;
  else:
      isDarkTheme = True;
  
  displayBgColor = None
  displayFontColor = None
  iconThemeFolder = None;
  
  if(isDarkTheme == False):
      displayBgColor = "#FFFFFF"
      displayFontColor = "#000000"
      iconThemeFolder="theme-light"
  else:
      displayBgColor = "#000000"
      displayFontColor = "#DDDDDD"
      iconThemeFolder="theme-dark"
  
  image, draw = createBlankImage(screenWidth, screenHeight, displayBgColor)
  fontNormal = ImageFont.truetype("droid-sans.regular.ttf", size=12)
  fontBig = ImageFont.truetype("droid-sans.bold.ttf", size=12)
  
  if(aq_values == None):
      drawTextCenter(
        draw=draw, 
        font=fontNormal, 
        top=50, 
        padding=leftRightPadding, 
        rowwidth=screenWidth, 
        text="Accuweather Error", 
        color="#FF0000"
      )
  else:
        
      for i in range(len(aq_values)):   
          drawTextLeft(
            draw=draw, 
            font=fontNormal, 
            top=5 + (17 * i), 
            padding=leftRightPadding, 
            rowwidth=screenWidth, 
            text="{label} | {value}".format(label="".join(aq_values[i][0].split(" ")), index=aq_values[i][1], value=aq_values[i][2]), 
            color=get_aq_value_index_color(int(aq_values[i][1]))
          )
          
      
      all_aq_indexes = list(map(lambda x: int(x[1]), aq_values))
      
      max_aq_index = max(all_aq_indexes)
      drawImageRight(
        top=56,
        padding=leftRightPadding, 
        rowwidth=screenWidth, 
        targetImage=image, 
        imageToDraw=Image.open("icons/aq/{t}/{i}".format(i=get_aq_value_index_icon(max_aq_index), t=iconThemeFolder))
      )
      

  drawHorizontalRule(image=image, draw=draw, top=112, padding=3, thick=1, fill="black")
  

  if(fybra_device_values == None):
      drawTextCenter(
        draw=draw, 
        font=fontNormal, 
        top=128, 
        padding=leftRightPadding, 
        rowwidth=screenWidth, 
        text="Fybra Sensor Error", 
        color="#FF0000"
      )
  else:
      
      ppmCO2Inside = int(fybra_device_values[0].split(" ")[0])
      vocInside = int(fybra_device_values[3].split(" ")[0])
      currentAQIconIn = None

        
      if(ppmCO2Inside >= 2201 or vocInside >= 401):
        currentAQIconIn = "poisonous.bmp"
      elif((ppmCO2Inside >= 1701 and ppmCO2Inside <= 2200) or (vocInside >= 311 and vocInside <= 400)):
        currentAQIconIn = "very-poor.bmp"
      elif((ppmCO2Inside >= 1301 and ppmCO2Inside <= 1700) or (vocInside >= 231 and vocInside <= 310)):
        currentAQIconIn = "poor.bmp"
      elif((ppmCO2Inside >= 1001 and ppmCO2Inside <= 1300) or (vocInside >= 151 and vocInside <= 230)):
        currentAQIconIn = "moderate.bmp"
      elif((ppmCO2Inside >= 701 and ppmCO2Inside <= 1000) or (vocInside >= 71 and vocInside <= 150)):
        currentAQIconIn = "fair.bmp"
      elif(ppmCO2Inside <= 700 or vocInside <= 70):
        currentAQIconIn = "good.bmp"


      drawTextLeft(
        draw=draw, 
        font=fontNormal, 
        top=119, 
        padding=leftRightPadding, 
        rowwidth=screenWidth, 
        text="In CO2: " + str(ppmCO2Inside) + " ppm", 
        color=displayFontColor
      )

      
      drawTextLeft(
        draw=draw, 
        font=fontNormal, 
        top=138, 
        padding=leftRightPadding, 
        rowwidth=screenWidth, 
        text="In VOC: "+ str(vocInside), 
        color=displayFontColor
      )
      
      if currentAQIconIn != None:
          drawImageRight(
            top=127, 
            padding=leftRightPadding, 
            rowwidth=screenWidth, 
            targetImage=image, 
            imageToDraw=Image.open("icons/aq/{t}/{i}".format(i=currentAQIconIn, t=iconThemeFolder))
          )

  return image


def on_read_aq_data(fybra_device_values: list[str] | None, aq_values: list[list[str]] | None):
    #print(fybra_device_values)
    #print(aq_values)
    page_image = getPageOne(fybra_device_values, aq_values)
    ST7735.display_image(page_image)
    



lastDataUpdateTime = 0
updateInterval = 5*60

try:
    ST7735.init_gpio()  # Initialize GPIO
    ST7735.initialize_display()  # Initialize the display
    connect_and_read(tick_interval_seconds=10, nth_tick_to_refresh_fybra=1, nth_tick_to_refresh_aq=1, callback=on_read_aq_data)
except Exception as e:
        print("\nGeneric Error.\n")
        #This line opens a log file
        with open("startpy_log.txt", "w") as log:
            traceback.print_exc(file=log)
            traceback.print_exc()
finally:
   ST7735.cleanup_gpio()


