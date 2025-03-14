import hashlib

from PIL import Image
from PIL import ImageDraw
import io

from app.services.interfaces.iimage_service import ImageService


class ImageGenerator(ImageService):
    def get_default(self):
        img = Image.new('RGB', (128, 128), (255, 255, 255))
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io

    def get_avatar(self, username: str):
        """Generate a simple procedural avatar based on the username."""
        size = 128

        # Hash the username to create a deterministic pattern
        hash_digest = hashlib.md5(username.encode()).hexdigest()
        r = int(hash_digest[:2], 16)
        g = int(hash_digest[2:4], 16)
        b = int(hash_digest[4:6], 16)

        # Create a base image with the hashed color
        img = Image.new('RGB', (size, size), (r, g, b))
        draw = ImageDraw.Draw(img)

        generation_size = 3

        # Generate fractal-like pattern using iterative hashing
        for i in range(generation_size):  # More iterations = more complexity
            for j in range(generation_size):
                # Hash variations for each block
                sub_hash = hashlib.md5((username + f"{i}{j}").encode()).hexdigest()
                r2 = int(sub_hash[:2], 16)
                g2 = int(sub_hash[2:4], 16)
                b2 = int(sub_hash[4:6], 16)

                # Determine block size
                block_size = size // generation_size
                x0, y0 = i * block_size, j * block_size
                x1, y1 = x0 + block_size, y0 + block_size

                # Draw squares with unique colors
                draw.rectangle([x0, y0, x1, y1], fill=(r2, g2, b2))

                # Add a circle inside the square (pseudo-fractal feel)
                if (r2 + g2 + b2) % 3 == 0:  # Randomized condition
                    draw.ellipse([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=(255 - r2, 255 - g2, 255 - b2))

        # Save image to a buffer
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io
