from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw
import ifcfg
import socket
import os
import shutil 
import getpass
import psutil

inky = auto()
inky.set_border(inky.WHITE)
fa_regular_brands = './Font Awesome 6 Brands-Regular-400.otf'
dejavu_sans = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
dejavu_sans_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-.ttf'
img = Image.new("P", (inky.WIDTH, inky.HEIGHT))
draw = ImageDraw.Draw(img)

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f'{round(size)}{power_labels[n]}'

def draw_host(draw, xy):
    font_logo = ImageFont.truetype(fa_regular_brands, 24)
    font_text = ImageFont.truetype(dejavu_sans, 24)
    hostname = socket.gethostname()
    rpi_logo = '\uf7bb'

    # measure up
    logo_width, logo_height = font_logo.getsize(rpi_logo)
    logo_width += 3 # add some space after
    text_width, text_height = font_text.getsize(hostname)
    content_height = max(logo_height, text_height)

    # draw a box big enough to have the text and logo with padding
    x, y = xy
    box_width = x + logo_width + text_width + 10, # start + logo + host name + padding
    box_height = y + content_height + 10 # start + text height + padding
    draw.rounded_rectangle(
            xy = [(x,y),(x + box_width, y + box_height)],
            fill = inky.RED,
            outline = inky.BLACK,
            width = 2,
            radius = 5)

    # draw the logo and hostname
    x += 5 # padding
    y += 5 + (content_height / 2) # padding and align in the center of the text
    draw.text((x, y+2), rpi_logo, inky.WHITE, font_logo, 'lm') # logo, +2 to allow for ascenders/decenders alignment
    x += logo_width
    draw.text((x,y), hostname, inky.WHITE, font_text, 'lm') 
    return (box_width + xy[0], box_height + xy[1])

if(getpass.getuser() == 'root'):
    os.system('umount /usbdisk.d')
    os.system('mount -o loop -t exfat /usbdisk.img /usbdisk.d')

usage = shutil.disk_usage("/usbdisk.d")

def draw_usage_text(draw, xy, usage):
    font = ImageFont.truetype(dejavu_sans_bold,13)

    # measure up
    labels = 'Used\nFree\nTotal'
    label_width, label_height = draw.multiline_textsize(
                text = labels, 
                font = font, 
                spacing = 2)

    values = (f'{format_bytes(usage.used)}\n'+
            f'{format_bytes(usage.free)}\n'+
            f'{format_bytes(usage.total)}')

    value_width, _ = draw.multiline_textsize(
                text = values, 
                font = font, 
                spacing = 2)
    
    box_width = label_width + value_width + 3 + 10 # border, text width, box padding 
    box_height = label_height + 10 # text height + padding

    # draw the box
    _, y = xy
    x = inky.WIDTH - box_width - 3 # border, text width, box padding 

    draw.rounded_rectangle(
            xy = [(x,y),(x + box_width, y + box_height)],
            fill = inky.RED,
            outline = inky.BLACK,
            width = 2,
            radius = 5)
    x += 5
    y += 5
    draw.multiline_text(xy = (x,y), 
                        text = labels, 
                        fill = inky.WHITE, 
                        font = font,
                        align = 'left')
    x += label_width + 3
    draw.multiline_text(xy = (x, y), 
                        text = values, 
                        fill = inky.WHITE, 
                        font = font,
                        align = 'right')
    return (box_width + xy[0], box_height + xy[1])

def draw_usage_chart(draw, xy, usage):
    # find the biggest box for the pie chart
    x,y = xy
    chart_size = min( 
                inky.WIDTH - x,
                inky.HEIGHT - y)
    chart_size -= 10 
    x += 5
    y += 5
    draw.ellipse(xy =  [(x, y), (x + chart_size, y + chart_size)],
                 outline = inky.BLACK, 
                 fill = inky.WHITE, 
                 width = 2)

    x += 1
    y += 1
    chart_size -= 2
    draw.pieslice(xy = [(x , y), (x + chart_size, y + chart_size)],
                outline = inky.RED,
                fill = inky.RED, 
                width = 2,
                start = 0,
                end = (usage.used/usage.total) * 360)
    return (inky.WIDTH - 1, inky.HEIGHT - 1)

y = titlebb + 10
font = ImageFont.truetype(dejavu_sans,13)
net = ifcfg.interfaces() 

# this is a dictionary. I want wlan0 and usb0, 
# but want to check if present first

if('wlan0' in net and 'inet' in net['wlan0'] 
          and net['wlan0']['inet'] is not None): 
    font_awesome_solid = ImageFont.truetype('./Font Awesome 6 Free-Solid-900.otf', 16)
    w, h = font_awesome_solid.getsize('\uf1eb')
    draw.text((5, y), '\uf1eb', inky.RED, font_awesome_solid)
    draw.text((w + 10, y), net['wlan0']['inet'], inky.BLACK, font)
    y += h + 3
fa_regular_brands = './Font Awesome 6 Brands-Regular-400.otf'
if('usb0' in net and 'inet' in net['usb0'] 
         and net['usb0']['inet'] is not None): 
    font_awesome_brands = ImageFont.truetype(fa_regular_brands, 16)
    w, h = font_awesome_brands.getsize('\uf287')
    draw.text((5, y), '\uf287', inky.RED, font_awesome_brands)
    draw.text((w + 10, y), net['usb0']['inet'], inky.BLACK, font)
    y += h + 3

y += 5
font = ImageFont.truetype(dejavu_sans,10)
def draw_text(xy, text, color, font):
    w,h = font.getsize(text)
    draw.text(xy, text, color, font)
    return (w, h)
for user in psutil.users():
    y += 2
    x = 5
    hMax = 0
    w, h = draw_text((x, y), '[', inky.RED, font)
    x += w
    hMax = max(hMax, h)
    w, h = draw_text((x, y), user.name, inky.BLACK, font)
    x += w
    hMax = max(hMax, h)
    w, h = draw_text((x, y), '@', inky.RED, font)
    x += w
    hMax = max(hMax, h)
    host = user.terminal[:3] if user.host == '' else user.host
    w, h = draw_text((x, y), host, inky.BLACK, font)
    x += w
    hMax = max(hMax, h)
    w, h = draw_text((x, y), ']', inky.RED, font)
    hMax = max(hMax, h)
    y += hMax    


inky.set_image(img)
inky.show()
