import os

from PIL import Image, ImageDraw, ImageFont
import pytesseract

class OCRcleaner:
    def __init__(self, font_file = 'OCR.TTF', font_size = 25, font_gap = 5):

        if not os.path.isfile(font_file):
            raise FileNotFoundError(f'Cannot find font file {font_file}')

        self.font_size, self.font_gap = font_size, font_gap
        self.image_height = font_size + (font_gap*2)
        self.font = ImageFont.truetype('OCR.TTF', size=font_size)

    def _ocr(self, img):
        return pytesseract.image_to_string(img, config='--psm 7').split('\n')[0]

    def _pict(self, message):
        img = Image.new(mode='RGB', size=(len(message)*self.font_size, self.image_height), color = 'white')
    
        draw = ImageDraw.Draw(img)
        draw.text((self.font_gap, self.font_gap), message, font=self.font, fill=(0,0,0))

        return img
    
    def __call__(self, msg):
        return self._ocr(self._pict(msg.replace('\n', '')))