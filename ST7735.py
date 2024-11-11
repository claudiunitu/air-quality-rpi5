import spidev
from PIL import Image
import gpiod
from gpiod.line import Direction, Value

# GPIO configuration
DC_PIN = 6  # Data/Command pin
RST_PIN = 5  # Reset pin

# Initialize SPI
spi = spidev.SpiDev(0, 0)  # Using SPI0 (Bus 0, Device 0)
spi.max_speed_hz = 40000000  # SPI speed (40 MHz)

# Configure GPIO lines using gpiod
def init_gpio():
    """Initialize GPIO pins."""
    global request
    request = gpiod.request_lines(
        "/dev/gpiochip4",  # Adjust this if needed
        consumer="st7735-display",
        config={
            DC_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
            RST_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)
        }
    )

def cleanup_gpio():
    """Cleanup GPIO pins when done."""
    global request
    request.release()

def send_command(command, data=None):
    """Send command to the display."""
    request.set_value(DC_PIN, Value.INACTIVE)  # Command mode
    spi.writebytes([command])
    if data:
        request.set_value(DC_PIN, Value.ACTIVE)  # Data mode
        spi.writebytes(data)

def initialize_display():
    """Initialize the display with a full sequence of commands."""
    # Hardware reset
    request.set_value(RST_PIN, Value.INACTIVE)
    request.set_value(RST_PIN, Value.ACTIVE)

    # Start initialization sequence
    send_command(0x01)        # Software reset
    send_command(0x11)        # Sleep out
    send_command(0x3A, [0x05])  # Set color mode to 16-bit RGB565
    send_command(0x36, [0xC0])  # Memory data access control (MADCTL), rotate the screen if needed
    send_command(0x29)        # Display on

def set_address_window():
    """Set the address window for the full screen."""
    # Set the column address range (0 to 127)
    send_command(0x2A, [0x00, 0x00, 0x00, 0x7F])  # Column address set (0x00 to 0x7F)
    
    # Set the row address range (0 to 159)
    send_command(0x2B, [0x00, 0x00, 0x00, 0x9F])  # Row address set (0x00 to 0x9F)
    
    send_command(0x2C)  # Memory write command

def display_image(image: Image):
    """Displays an image on the display."""

    # Convert image to RGB565 format
    pixel_data = []
    for r, g, b in image.getdata():
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        pixel_data.append(rgb565 >> 8)  # High byte
        pixel_data.append(rgb565 & 0xFF)  # Low byte

    set_address_window()

    # Send pixel data in chunks
    chunk_size = 4096
    request.set_value(DC_PIN, Value.ACTIVE)  # Data mode
    for i in range(0, len(pixel_data), chunk_size):
        spi.writebytes(pixel_data[i:i + chunk_size])

def display_image_from_path(image_path):
    """Displays an image on the display."""
    image = Image.open(image_path).resize((128, 160)).convert('RGB')
    display_image(image)

def fill_screen(color):
    """Fill the screen with a single color."""
    set_address_window()

    # Prepare color data (RGB565)
    red, green, blue = color
    color_data = [(red >> 3) << 8 | (green >> 2) << 3 | (blue >> 3)] * (128 * 160)
    color_data = [byte for word in color_data for byte in (word >> 8, word & 0xFF)]  # RGB565 to byte array

    chunk_size = 4096
    request.set_value(DC_PIN, Value.ACTIVE)  # Data mode
    for i in range(0, len(color_data), chunk_size):
        spi.writebytes(color_data[i:i + chunk_size])

# Example usage
if __name__ == "__main__":
    

    try:
        init_gpio()  # Initialize GPIO
        initialize_display()  # Initialize the display
        #display_image_from_path('icons/aq/theme-dark/fair.bmp')  # Display an image
        pillow_custom_image = Image.new("RGB", (128, 160), "#00aa00")
        display_image(pillow_custom_image)

    finally:
        cleanup_gpio()  # Make sure to cleanup GPIO after use
