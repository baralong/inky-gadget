from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw
import ifcfg
import socket
import os
import sys
import signal
import shutil 
import psutil
import inspect
from typing import NamedTuple
import time
import json

# Setup Inky
inky = auto()
inky.set_border(inky.WHITE)

# get the path the script is running in
my_dir = os.path.dirname(
             os.path.abspath(
                 inspect.getframeinfo(
                     inspect.currentframe()).filename)) 

# font names
fa_solid = f'{my_dir}/Font Awesome 6 Free-Solid-900.otf'
fa_regular = f'{my_dir}/Font Awesome 6 Free-Regular-400.otf'
fa_regular_brands = f'{my_dir}/Font Awesome 6 Brands-Regular-400.otf'
dejavu_sans = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
dejavu_sans_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# classes to store the data shown on the screen
class User(NamedTuple): # store for logged in users
    name: str
    host: str
class GadgetInfo(NamedTuple):
    host_name: str      # device name
    usage: shutil._ntuple_diskusage # mass storage usage
    users: list[User]   # list of logged in users
    wlan: str           # wifi address
    usb: str            # usb address

# Query the system to populate the gadget info
def get_gadget_info() -> GadgetInfo:
    # unmount and remount the usb backing store so we can know what it looks like
    if(os.geteuid() == 0):
        os.system('umount /usbdisk.d')
        os.system('mount -o loop -t exfat /usbdisk.img /usbdisk.d')
    
    # current network interfaces
    net = ifcfg.interfaces()

    return GadgetInfo( 
            host_name = socket.gethostname(),  
            usage = shutil.disk_usage("/usbdisk.d"),
            users = sorted(map(
                            lambda user: # maps the "users" list to our User Object
                                User(
                                    user.name,
                                    user.terminal[:3] if (user.host == '' and user.terminal != None) else user.host
                                ),
                                psutil.users())),

            wlan = (net['wlan0']['inet']) if (
                'wlan0' in net and 'inet' in net['wlan0']
                ) else None, # address if we're connected to wifi
                
            usb = (net['usb0']['inet']) if (
                'usb0' in net and 'inet' in net['usb0']
                ) else None # address if connected by the ethernet gadget
        )

# Convert raw byte count into sensible numbers
def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f'{round(size)}{power_labels[n]}'

### draw_* functions
### All draw_* functions have a similar form
###    First 2 parameters:
###        draw: ImageDraw object based on an image the size of the InkyPhat
###              https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html
###        xy: Tuple[int,int] the top left corner to start the item drawn
###    Returns:
###        xy: Tuple[int,int] the bottom right corner of the item drawn

# draw the raspberry pi logo and hostname at xy
def draw_host(draw, xy, hostname):
    font_logo = ImageFont.truetype(fa_regular_brands, 24)
    rpi_logo = '\uf7bb' # the font awesome brands font contains the Raspberry Pi logo at unicode F7BB
    font_text = ImageFont.truetype(dejavu_sans, 24)

    # measure up how much space we need for the text and logo
    _, _, logo_width, logo_height = font_logo.getbbox(rpi_logo)
    logo_width += 3 # add some space after
    _, _, text_width, text_height = font_text.getbbox(hostname)
    content_height = max(logo_height, text_height)

    # draw a box big enough to have the text and logo with padding
    x, y = xy
    box_width = logo_width + text_width + 10 # start + logo + host name + padding
    box_height = content_height + 10         # start + text height + padding
    draw.rounded_rectangle(                  # the background for the host name
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

# Draw the table and pie chart of the disk usage of the mass storage device
def draw_usage_text(draw, xy, usage):
    font = ImageFont.truetype(dejavu_sans_bold,13)

    # measure up all the text to see how much space we need
    labels = 'Used\nFree\nTotal'
    _, _, label_width, label_height = draw.multiline_textbbox(
                xy = (0,0),
                text = labels, 
                font = font, 
                spacing = 2)

    values = (f'{format_bytes(usage.used)}\n'+
              f'{format_bytes(usage.free)}\n'+
              f'{format_bytes(usage.total)}')

    _,_,value_width,_ = draw.multiline_textbbox( # it's still 3 lines of text, so we don't need to measure the height
                xy = (0,0),
                text = values, 
                font = font, 
                spacing = 2)
    
    # calculate box size and position
    box_width = label_width + value_width + 3 + 10 # border, text width, box padding 
    box_height = label_height + 12 # text height + padding

    _, y = xy # we ignore the x position as we're fitting things into the right side fo the screen
    x = inky.WIDTH - box_width - 5 # border, text width, box padding 

    # draw the box, 
    draw.rounded_rectangle(
            xy = [(x,y),(x + box_width, y + box_height)],
            fill = inky.RED,
            outline = inky.BLACK,
            width = 2,
            radius = 5)
    # add padding
    x += 5
    y += 3
    # draw the labels
    draw.multiline_text(xy = (x,y), 
                        text = labels, 
                        fill = inky.WHITE, 
                        font = font,
                        align = 'left')
    x += label_width + 3 # add padding
    # draw the values
    draw.multiline_text(xy = (x, y), 
                        text = values, 
                        fill = inky.WHITE, 
                        font = font,
                        align = 'right')
    return (box_width + xy[0], box_height + xy[1])

# draw the pie chart of usage in the bottom left of the screen
def draw_usage_chart(draw, xy, usage):
    # find the biggest box for the pie chart
    x,y = xy
    chart_size = min( 
                inky.WIDTH - x,
                inky.HEIGHT - y)

    chart_size -= 10 # allow for padding

    x = (x + inky.WIDTH - chart_size) / 2  # left edge of the circle
    y = (y + inky.HEIGHT - chart_size) / 2 # top of the circle

    # draw the outer circle
    draw.ellipse(xy =  [(x, y), (x + chart_size, y + chart_size)],
                 outline = inky.BLACK, 
                 fill = inky.WHITE, 
                 width = 2)

    # reduce the size by 1 pixel at each end
    x += 1
    y += 1
    chart_size -= 2

    # draw the pie slice of the used space
    draw.pieslice(xy = [(x , y), (x + chart_size, y + chart_size)],
                outline = inky.RED,
                fill = inky.RED, 
                width = 2,
                start = 0,
                end = (usage.used/usage.total) * 360)
                
    # we filled the bottom left
    return (inky.WIDTH - 1, inky.HEIGHT - 1)

# draw some text in a particular color and font
def draw_text(draw, xy, text, color, font):
    _, _, w,h = font.getbbox(text)
    draw.text(xy, text, color, font)
    return (w+xy[0], h+xy[1])

# draw an icon in red and text in black with 3 pixel padding
def draw_icon_text(draw, xy, icon_font, icon_text, interface_font, interface_text):
    x, y_icon = draw_text(draw, xy, icon_text, inky.RED, icon_font)
    x, y_text = draw_text(draw, (x + 3, xy[1]), interface_text, inky.BLACK, interface_font)
    return (x, max(y_icon, y_text))

# draw the list of users currently logged in, left aligned at x
def draw_users(draw, xy, users: list[User]):
    icon = ImageFont.truetype(fa_solid, 14)
    font = ImageFont.truetype(dejavu_sans,12)
    x,y = xy
    y_max = 0
    x_max = 0
    for user in users:
        x, _ = xy # start the the left again
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
            # Off the bottom of the screen, stop drawing
            break    
        return (x_max, y_max)

# draw the owner details in the bottom left, but the same width as the host name
def draw_owner(draw, xy, x_max: int):
    global my_dir
    # get the data from the USB or default
    owner = {}
    usb_file = '/usbdisk.d/owner.json'    # get it from the mass storage if it exists
    default_file = f'{my_dir}/owner.json' # default

    # find the data file
    data_file = usb_file if os.path.exists(usb_file) else default_file
    try:
        owner = json.load(open(data_file))
    except:
        print(f'Load of {data_file} failed')
                
    # draw the background box
    x, y = xy
    draw.rounded_rectangle(
            xy = [(x,y),(x_max, inky.HEIGHT)],
            fill = inky.WHITE,
            outline = inky.RED,
            width = 2,
            radius = 5)
    # padding
    x += 5
    y += 5
    if "name" in owner:
        _, y = draw_icon_text(draw, (x,y),
                      ImageFont.truetype(fa_solid, 12), '\uf4fb', # spaceman icon
                      ImageFont.truetype(dejavu_sans_bold, 12), owner["name"])
        y += 2

    if "email" in owner:
        _, y = draw_icon_text(draw, (x,y),
                      ImageFont.truetype(fa_regular, 12), '\uf0e0', # envelope icon
                      ImageFont.truetype(dejavu_sans, 11), owner["email"])
        y += 2

    if "phone" in owner:
        _, y = draw_icon_text(draw, (x,y),
                      ImageFont.truetype(fa_solid, 12), '\uf095', # phone icon
                      ImageFont.truetype(dejavu_sans, 12), owner["phone"])
        y += 2

    if "twitter" in owner:
        _, y = draw_icon_text(draw, (x,y),
                      ImageFont.truetype(fa_regular_brands, 12), '\uf099',  # twitter icon
                      ImageFont.truetype(dejavu_sans, 12), owner["twitter"])

# redraw the whole screen
#     gadget_info: GadgetInfo -> the data to draw
#     shutdown: bool -> triggered by a shutdown
def draw_info(gadget_info: GadgetInfo, shutdown: bool):
    # an image the size of the screen
    img = Image.new("P", (inky.WIDTH, inky.HEIGHT))
    # drawing object
    draw = ImageDraw.Draw(img)

    # Host
    x = 5
    y = 10
    xd,y = draw_host(draw, (x,y), gadget_info.host_name)
    y += 5
    x_max = xd

    # system IP addresses
    if not shutdown and gadget_info.wlan != None:
        xd, y = draw_icon_text(draw, (x,y), 
                          ImageFont.truetype(fa_solid, 16), '\uf1eb', # wifi logo
                          ImageFont.truetype(dejavu_sans, 14), gadget_info.wlan)
        x_max = max(x_max, xd)
        y += 3
    
    if not shutdown and gadget_info.usb != None:
        xd, y = draw_icon_text(draw, (x,y), 
                          ImageFont.truetype(fa_regular_brands, 16), '\uf287',  # usb logo
                          ImageFont.truetype(dejavu_sans, 14), gadget_info.usb)
        x_max = max(x_max, xd)
        y += 3

    # users logged in
    if not shutdown and len(gadget_info.users) > 0:
        xd, _ = draw_users(draw, (x,y), gadget_info.users)
        x_max = max(x_max, xd)

    # draw the owner info, but only if we're shutting down or we have nothing else to show
    if shutdown or (gadget_info.wlan == None and gadget_info.usb == None and len(gadget_info.users) == 0):
        draw_owner(draw, (x,y), x_max)

    # Draw the usage text and chart
    x = x_max
    y = 10
    _,y = draw_usage_text(draw, (x,y), gadget_info.usage)
    draw_usage_chart(draw, (x,y), gadget_info.usage)

    # all drawn, get it to display
    inky.set_image(img)
    inky.show()

# start knowing nothing
current_info = GadgetInfo(None,None,None,None,None)

# if we're shutting down gracefully, draw the owner info
def exit_gracefully(signum, frame):
    global current_info
    draw_info(current_info, True)
    time.sleep(16) # the drawing isn't blocking, so we have to wait for it to finish
    sys.exit(0)


signal.signal(signal.SIGINT, exit_gracefully)  # keyboard interrupt
signal.signal(signal.SIGTERM, exit_gracefully) # terminate interrupt
while True:
    new_info = get_gadget_info()
    if current_info != new_info:
        current_info = new_info
        draw_info(current_info, False)
    time.sleep(30)
