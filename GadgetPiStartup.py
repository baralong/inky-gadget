from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw
import ifcfg
import socket
import os
import signal
import shutil 
import psutil
from typing import NamedTuple
import time

# globals
inky = auto()
inky.set_border(inky.WHITE)
fa_solid = './Font Awesome 6 Free-Solid-900.otf'
fa_regular = './Font Awesome 6 Free-Regular-400.otf'
fa_regular_brands = './Font Awesome 6 Brands-Regular-400.otf'
dejavu_sans = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
dejavu_sans_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
owner_name = 'Doug Paice'
owner_email = 'doug@baralong.org'
owner_twitter = '@baralong'
owner_phone = '+61 421 708 171'

class User(NamedTuple):
    name: str
    host: str
class GadgetInfo(NamedTuple):
    host_name: str
    usage: shutil._ntuple_diskusage
    users: list[User]
    wlan: str
    usb: str

def get_gadget_info() -> GadgetInfo:
    if(os.geteuid() == 0):
        os.system('umount /usbdisk.d')
        os.system('mount -o loop -t exfat /usbdisk.img /usbdisk.d')
    net = ifcfg.interfaces()

    return GadgetInfo( 
            host_name = socket.gethostname(),
            usage = shutil.disk_usage("/usbdisk.d"),
            users = sorted(map(
                            lambda user:
                                User(
                                    user.name,
                                    user.terminal[:3] if (user.host == '' and user.terminal != None) else user.host
                                ),
                                psutil.users())),

            wlan = (net['wlan0']['inet']) if (
                'wlan0' in net and 'inet' in net['wlan0']
                ) else None,
                
            usb = (net['usb0']['inet']) if (
                'usb0' in net and 'inet' in net['usb0']
                ) else None
        )

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f'{round(size)}{power_labels[n]}'

def draw_host(draw, xy, hostname):
    font_logo = ImageFont.truetype(fa_regular_brands, 24)
    font_text = ImageFont.truetype(dejavu_sans, 24)
    rpi_logo = '\uf7bb'

    # measure up
    logo_width, logo_height = font_logo.getsize(rpi_logo)
    logo_width += 3 # add some space after
    text_width, text_height = font_text.getsize(hostname)
    content_height = max(logo_height, text_height)

    # draw a box big enough to have the text and logo with padding
    x, y = xy
    box_width = logo_width + text_width + 10 # start + logo + host name + padding
    box_height = content_height + 10 # start + text height + padding
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
    box_height = label_height + 12 # text height + padding

    # draw the box
    _, y = xy
    x = inky.WIDTH - box_width - 5 # border, text width, box padding 

    draw.rounded_rectangle(
            xy = [(x,y),(x + box_width, y + box_height)],
            fill = inky.RED,
            outline = inky.BLACK,
            width = 2,
            radius = 5)
    x += 5
    y += 3
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
    x = (x + inky.WIDTH - chart_size) / 2 
    y = (y + inky.HEIGHT - chart_size) / 2
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

def draw_text(draw, xy, text, color, font):
    w,h = font.getsize(text)
    draw.text(xy, text, color, font)
    return (w+xy[0], h+xy[1])

def draw_icon_text(draw, xy, icon_font, icon_text, interface_font, interface_text):
    x, y_icon = draw_text(draw, xy, icon_text, inky.RED, icon_font)
    x, y_text = draw_text(draw, (x + 3, xy[1]), interface_text, inky.BLACK, interface_font)
    return (x, max(y_icon, y_text))

def draw_users(draw, xy, users: list[User]):
    icon = ImageFont.truetype(fa_solid, 14)
    font = ImageFont.truetype(dejavu_sans,12)
    x,y = xy
    y_max = 0
    x_max = 0
    for user in users:
        y += 2
        x += 5
        x, yd = draw_text(draw, (x, y + 2), '\uf120', inky.RED, icon)
        x += 5
        y_max = yd
        x, yd = draw_text(draw, (x, y), '[', inky.RED, font)
        y_max = yd
        x, yd = draw_text(draw, (x, y), user.name, inky.BLACK, font)
        y_max = max(y_max, yd)
        x, yd = draw_text(draw, (x, y), '@', inky.RED, font)
        y_max = max(y_max, yd)
        x, yd = draw_text(draw, (x, y), user.host, inky.BLACK, font)
        y_max = max(y_max, yd)
        x, yd = draw_text(draw, (x, y), ']', inky.RED, font)
        y_max = max(y_max, yd) 
        y_max += 2 # spacing
        x_max = max(x_max, x)
        if y_max > inky.HEIGHT:
            # went too far
            break    
        return (x_max, y_max)

def draw_owner(draw, xy, x_max: int,  shutdown: bool):
    # draw something to show current state, either on or off
    x, y = xy
    draw.rounded_rectangle(
            xy = [(x,y),(x_max, inky.HEIGHT - 4)],
            fill = inky.WHITE,
            outline = inky.RED,
            width = 2,
            radius = 5)
    x += 5
    y += 5
    _, y = draw_icon_text(draw, (x,y),
                          ImageFont.truetype(fa_solid, 12), '\uf4fb', 
                          ImageFont.truetype(dejavu_sans_bold, 12), owner_name)
    y += 2
    _, y = draw_icon_text(draw, (x,y),
                          ImageFont.truetype(fa_regular, 12), '\uf0e0', 
                          ImageFont.truetype(dejavu_sans, 11), owner_email)
    y += 2
    _, y = draw_icon_text(draw, (x,y),
                          ImageFont.truetype(fa_solid, 12), '\uf095', 
                          ImageFont.truetype(dejavu_sans, 12), owner_phone)
    y += 2
    _, y = draw_icon_text(draw, (x,y),
                          ImageFont.truetype(fa_regular_brands, 12), '\uf099', 
                          ImageFont.truetype(dejavu_sans, 12), owner_twitter)

def draw_info(gadget_info: GadgetInfo, shutdown: bool):
    img = Image.new("P", (inky.WIDTH, inky.HEIGHT))
    draw = ImageDraw.Draw(img)
    # left side
    x = 5
    y = 5
    xd,y = draw_host(draw, (x,y), gadget_info.host_name)
    y += 5
    x_max = xd

    if not shutdown and gadget_info.wlan != None:
        xd, y = draw_icon_text(draw, (x,y), 
                          ImageFont.truetype(fa_solid, 16), '\uf1eb', 
                          ImageFont.truetype(dejavu_sans, 14), gadget_info.wlan)
        x_max = max(x_max, xd)
        y += 3
    
    if not shutdown and gadget_info.usb != None:
        xd, y = draw_icon_text(draw, (x,y), 
                          ImageFont.truetype(fa_regular_brands, 16), '\uf287', 
                          ImageFont.truetype(dejavu_sans, 14), gadget_info.usb)
        x_max = max(x_max, xd)
        y += 3

    if not shutdown and len(gadget_info.users) > 0:
        xd, _ = draw_users(draw, (x,y), gadget_info.users)
        x_max = max(x_max, xd)

    if shutdown or (gadget_info.wlan == None and gadget_info.usb == None and len(gadget_info.users) == 0):
        draw_owner(draw, (x,y), x_max,  shutdown)
    # right side
    x = x_max
    y = 5
    _,y = draw_usage_text(draw, (x,y), gadget_info.usage)
    draw_usage_chart(draw, (x,y), gadget_info.usage)

    inky.set_image(img)
    inky.show()
    time.sleep(15)

current_info = GadgetInfo(None,None,None,None,None)
exit_gracefully = lambda _: draw_info(current_info, True)
signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
while True:
    new_info = get_gadget_info()
    if current_info != new_info:
        current_info = new_info
        draw_info(current_info, False)
    time.sleep(30)
