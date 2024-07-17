import random
from PIL import Image, ImageDraw, ImageFilter
import time


def generate_test_image():
    image_size = (800, 600)
    num_circles = 50
    blur_radius = 20

    # create a random rgb color

    # Create a new image with white background
    rand_image = Image.new('RGB', image_size, "white")
    draw = ImageDraw.Draw(rand_image)

    # Generate and draw random circles
    generate_circles(draw, image_size, num_circles)

    # Apply a slight blur to the image
    rand_image = rand_image.filter(ImageFilter.GaussianBlur(blur_radius))

    draw = ImageDraw.Draw(rand_image)  # Get a new drawing context to add text
    generate_circles(draw, image_size, 10)

    return rand_image


def generate_circles(draw, image_size, num_circles):
    for _ in range(num_circles):
        circle_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        radius = random.randint(10, 100)  # Random radius between 10 and 100
        position = (random.randint(0, image_size[0] - radius * 2),
                    random.randint(0, image_size[1] - radius * 2))
        draw.ellipse([position, (position[0] + radius * 2, position[1] + radius * 2)],
                     fill=circle_color)


if __name__ == '__main__':
    image = generate_test_image()
    image.show()
    image.save(f"test_image_{int(time.time())}.png")
