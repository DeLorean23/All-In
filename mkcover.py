import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, out, text = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(src).convert("RGB")
d = ImageDraw.Draw(im)
# clear the inner part of the bottom bar (dark interior)
d.polygon([(86,670),(714,670),(731,700),(714,731),(86,731),(69,700)], fill=(6,4,14))
d.rectangle((68,709,80,722), fill=(6,4,14)); d.rectangle((720,683,732,695), fill=(6,4,14))
font = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-BoldItalic.ttf", int(sys.argv[4]) if len(sys.argv)>4 else 54)
bb = d.textbbox((0,0), text, font=font)
w, h = bb[2]-bb[0], bb[3]-bb[1]
x, y = 400 - w//2 - bb[0], 700 - h//2 - bb[1]
# glow
glow = Image.new("RGB", im.size, (0,0,0))
ImageDraw.Draw(glow).text((x,y), text, font=font, fill=(255,40,200))
glow = glow.filter(ImageFilter.GaussianBlur(6))
im = Image.composite(Image.blend(im, glow, 0), im, Image.new("L", im.size, 0))
from PIL import ImageChops
im = ImageChops.add(im, glow)
# chrome gradient (white -> pink)
mask = Image.new("L", im.size, 0)
ImageDraw.Draw(mask).text((x,y), text, font=font, fill=255)
grad = Image.new("RGB", im.size)
gd = ImageDraw.Draw(grad)
for yy in range(im.size[1]):
    t = min(max((yy-(y+bb[1]))/max(h,1),0),1)
    c = (255, int(255-90*t), int(255-40*t))
    gd.line([(0,yy),(im.size[0],yy)], fill=c)
im.paste(grad, (0,0), mask)
# thin magenta outline
ol = mask.filter(ImageFilter.MaxFilter(3))
edge = ImageChops.subtract(ol, mask)
im.paste((200,30,170), (0,0), edge)
im.save(out)
