from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw
import ifcfg
import socket
import os
import shutil 
import getpass
import psutil

def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f'{round(size)}{power_labels[n]}'

inky = auto()
inky.set_border(inky.WHITE)

img = Image.new("P", (inky.WIDTH, inky.HEIGHT))
draw = ImageDraw.Draw(img)
font_awesome_brands = ImageFont.truetype('./Font Awesome 6 Brands-Regular-400.otf', 24)
font_dejavu = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
y = 5
x = 5
hostname = socket.gethostname()
rpi = '\uf7bb'
piw, pih = font_awesome_brands.getsize(rpi)
hostw, hosth = font_dejavu.getsize(hostname)
texth = max(pih, hosth)
# draw a box around the text with 5 pixel padding
draw.rounded_rectangle([(x,y),(x+piw+hostw+12, y+texth+10)],
                       5, inky.RED, inky.BLACK, 2)
titlebb = y+texth+10
x += 5
y += 5 + (texth / 2)
draw.text((x, y+2), rpi, inky.WHITE, font_awesome_brands, 'lm')
x += piw + 3
draw.text((x,y), hostname, inky.WHITE, font_dejavu, 'lm')

if(getpass.getuser() == 'root'):
    os.system('umount /usbdisk.d')
    os.system('mount -o loop -t exfat /usbdisk.img /usbdisk.d')
    #print('remounted')

usage = shutil.disk_usage("/usbdisk.d")
font_dejavu = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',13)

labels = 'Used\nFree\nTotal'
lw,lh = draw.multiline_textsize(
            text = labels, 
            font = font_dejavu, 
            spacing = 2)

values = (f'{format_bytes(usage.used)}\n'+
          f'{format_bytes(usage.free)}\n'+
          f'{format_bytes(usage.total)}')

vw,vh = draw.multiline_textsize(
            text = values, 
            font = font_dejavu, 
            spacing = 2)
 
tx = inky.WIDTH - (lw + vw + 3) - 13 # border, text width, box padding 
ty = 10
draw.rounded_rectangle(
        xy = [(tx-5,ty-5),(inky.WIDTH-5, ty + lh + 10)],
        fill = inky.RED,
        outline = inky.BLACK,
        width = 2,
        radius = 5)
draw.multiline_text(xy = (tx,ty-1), 
                    text = labels, 
                    fill = inky.WHITE, 
                    font = font_dejavu,
                    align = 'left')
draw.multiline_text(xy = (inky.WIDTH - 10 - vw, ty-1), 
                    text = values, 
                    fill = inky.WHITE, 
                    font = font_dejavu,
                    align = 'right')

# find the biggest box for the pie chart
usageSize = min( 
             inky.WIDTH - tx - 5,
             inky.HEIGHT - (ty + lh + 10)) - 10
chartx = (inky.WIDTH + tx - usageSize) / 2
charty = inky.HEIGHT - usageSize - 4
draw.ellipse(xy =  [(chartx, charty), (chartx+usageSize, charty+usageSize)],
             outline = inky.BLACK, 
             fill = inky.WHITE, 
             width = 2)

++chartx
++charty
usageSize -= 2
draw.pieslice(xy = [(chartx, charty), (chartx+usageSize, charty+usageSize)],
             fill = inky.RED, 
             width = 2,
             start = 0,
             end = (usage.used/usage.total) * 360)

y = titlebb + 10
font_dejavu = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
net = ifcfg.interfaces() 

# this is a dictionary. I want wlan0 and usb0, 
# but want to check if present first

if('wlan0' in net and 'inet' in net['wlan0'] 
          and net['wlan0']['inet'] is not None): 
    font_awesome_solid = ImageFont.truetype('./Font Awesome 6 Free-Solid-900.otf', 16)
    w, h = font_awesome_solid.getsize('\uf1eb')
    draw.text((5, y), '\uf1eb', inky.RED, font_awesome_solid)
    draw.text((w + 10, y), net['wlan0']['inet'], inky.BLACK, font_dejavu)
    y += h + 3

if('usb0' in net and 'inet' in net['usb0'] 
         and net['usb0']['inet'] is not None): 
    font_awesome_brands = ImageFont.truetype('./Font Awesome 6 Brands-Regular-400.otf', 16)
    w, h = font_awesome_brands.getsize('\uf287')
    draw.text((5, y), '\uf287', inky.RED, font_awesome_brands)
    draw.text((w + 10, y), net['usb0']['inet'], inky.BLACK, font_dejavu)
    y += h + 3

y += 5
font_dejavu = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',10)
def draw_text(xy, text, color, font):
    w,h = font.getsize(text)
    draw.text(xy, text, color, font)
    return (w, h)
for user in psutil.users():
    y += 2
    x = 5
    hMax = 0
    w, h = draw_text((x, y), '[', inky.RED, font_dejavu)
    x += w
    hMax = max(hMax, h)
    w, h = draw_text((x, y), user.name, inky.BLACK, font_dejavu)
    x += w
    hMax = max(hMax, h)
    w, h = draw_text((x, y), '@', inky.RED, font_dejavu)
    x += w
    hMax = max(hMax, h)
    host = user.terminal[:3] if user.host == '' else user.host
    w, h = draw_text((x, y), host, inky.BLACK, font_dejavu)
    x += w
    hMax = max(hMax, h)
    w, h = draw_text((x, y), ']', inky.RED, font_dejavu)
    hMax = max(hMax, h)
    y += hMax    


inky.set_image(img)
inky.show()
