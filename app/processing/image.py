"""
Image processing utilities for grayscale to colorized PNG conversion.

This module provides vectorized operations for:
1. Color map LUT generation (256×3 RGB lookup table)
2. Image resizing (1×200 → 1×150 with bilinear interpolation)
3. Grayscale to RGB color mapping (vectorized via NumPy indexing)
"""

from io import BytesIO
from typing import Final

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from app.core import get_logger

logger = get_logger(__name__)

# Color stops for gradient (dark blue → cyan → green → yellow → red)
# These create a visually appealing depth colormap
COLOR_STOPS: Final[list[tuple[int, tuple[int, int, int]]]] = [
    (0, (0, 0, 128)),      # Dark blue (deep)
    (64, (0, 128, 255)),   # Cyan
    (128, (0, 255, 128)),  # Green
    (192, (255, 255, 0)),  # Yellow
    (255, (255, 0, 0)),    # Red (shallow)
]


def generate_colormap_lut() -> NDArray[np.uint8]:
    """
    Generate a 256×3 lookup table for grayscale to RGB color mapping.
    
    Creates a smooth gradient from dark blue (deep) through cyan, green, 
    yellow to red (shallow). Uses linear interpolation between color stops.
    
    Returns:
        NDArray[np.uint8]: Shape (256, 3) array where index [i] gives RGB 
        triple for grayscale value i
    
    Example:
        >>> lut = generate_colormap_lut()
        >>> lut[0]    # Dark blue for value 0
        array([  0,   0, 128], dtype=uint8)
        >>> lut[255]  # Red for value 255
        array([255,   0,   0], dtype=uint8)
    """
    # Initialize LUT array
    lut = np.zeros((256, 3), dtype=np.uint8)
    
    # Interpolate between each pair of color stops
    for i in range(len(COLOR_STOPS) - 1):
        start_idx, start_color = COLOR_STOPS[i]
        end_idx, end_color = COLOR_STOPS[i + 1]
        
        # Number of steps between stops
        num_steps = end_idx - start_idx
        
        # Linear interpolation for each RGB channel
        for channel in range(3):
            lut[start_idx:end_idx + 1, channel] = np.linspace(
                start_color[channel],
                end_color[channel],
                num_steps + 1,
                dtype=np.uint8
            )
    
    logger.debug("Generated colormap LUT", extra={"shape": lut.shape, "dtype": str(lut.dtype)})
    return lut


# Precompute and cache the colormap LUT at module load time
COLORMAP_LUT: Final[NDArray[np.uint8]] = generate_colormap_lut()


def apply_colormap(grayscale: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """
    Apply color map to grayscale image using vectorized LUT indexing.
    
    This is much faster than loops because it uses NumPy's advanced indexing
    to map all pixel values in a single operation.
    
    Args:
        grayscale: Grayscale image array with values 0-255, any shape
    
    Returns:
        NDArray[np.uint8]: RGB image with shape (*grayscale.shape, 3)
    
    Example:
        >>> gray = np.array([[0, 128, 255]], dtype=np.uint8)
        >>> rgb = apply_colormap(gray)
        >>> rgb.shape
        (1, 3, 3)  # 1 row, 3 pixels, 3 channels
    """
    # Vectorized lookup: COLORMAP_LUT[grayscale] returns RGB for each pixel
    return COLORMAP_LUT[grayscale]


def resize_grayscale_row(row: NDArray[np.uint8], target_width: int = 150) -> NDArray[np.uint8]:
    """
    Resize a single grayscale row from 200 to target width using bilinear interpolation.
    
    Converts 1D array to 2D image, resizes with high-quality interpolation,
    then returns as 1D array.
    
    Args:
        row: 1D grayscale array of shape (200,) with uint8 values
        target_width: Desired width (default 150)
    
    Returns:
        NDArray[np.uint8]: Resized 1D array of shape (target_width,)
    
    Example:
        >>> row = np.random.randint(0, 256, 200, dtype=np.uint8)
        >>> resized = resize_grayscale_row(row, 150)
        >>> resized.shape
        (150,)
    """
    # Create 1-pixel-tall image from row
    img = Image.fromarray(row.reshape(1, -1), mode='L')
    
    # Resize with bilinear interpolation (LANCZOS for highest quality)
    resized_img = img.resize((target_width, 1), Image.Resampling.LANCZOS)
    
    # Convert back to 1D array
    return np.array(resized_img).flatten()


def encode_to_png(rgb_array: NDArray[np.uint8]) -> bytes:
    """
    Encode RGB array to PNG bytes.
    
    Args:
        rgb_array: RGB image array of shape (height, width, 3)
    
    Returns:
        bytes: PNG-encoded image data
    
    Example:
        >>> rgb = np.random.randint(0, 256, (1, 150, 3), dtype=np.uint8)
        >>> png_bytes = encode_to_png(rgb)
        >>> len(png_bytes) > 0
        True
    """
    # Create PIL Image from RGB array
    img = Image.fromarray(rgb_array, mode='RGB')
    
    # Encode to PNG in memory
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    png_bytes = buffer.getvalue()
    
    logger.debug(
        "Encoded to PNG",
        extra={
            "input_shape": rgb_array.shape,
            "output_size_bytes": len(png_bytes)
        }
    )
    
    return png_bytes


def process_row_to_png(
    row_data: NDArray[np.float64] | list[float],
    source_width: int = 200,
    target_width: int = 150
) -> tuple[bytes, int, int]:
    """
    Complete pipeline: CSV row → resized colorized PNG.
    
    Steps:
    1. Convert to uint8 grayscale array (clamp to 0-255)
    2. Resize from source_width to target_width
    3. Apply colormap (grayscale → RGB)
    4. Encode to PNG bytes
    
    Args:
        row_data: Array or list of pixel values (0-255 range)
        source_width: Original width (default 200)
        target_width: Target width (default 150)
    
    Returns:
        tuple: (png_bytes, width, height)
            - png_bytes: PNG-encoded image data
            - width: Final image width (target_width)
            - height: Final image height (always 1)
    
    Example:
        >>> row = np.random.rand(200) * 255
        >>> png_bytes, width, height = process_row_to_png(row)
        >>> width, height
        (150, 1)
        >>> len(png_bytes) > 0
        True
    """
    # Convert to numpy array and ensure uint8 (0-255)
    grayscale = np.array(row_data, dtype=np.float64)
    grayscale = np.clip(grayscale, 0, 255).astype(np.uint8)
    
    # Ensure we have expected source width
    if len(grayscale) != source_width:
        raise ValueError(
            f"Expected {source_width} pixel values, got {len(grayscale)}"
        )
    
    # Step 1: Resize grayscale row
    resized_gray = resize_grayscale_row(grayscale, target_width)
    
    # Step 2: Apply colormap to get RGB
    # Reshape to (1, target_width) for 2D image, then apply colormap
    rgb = apply_colormap(resized_gray.reshape(1, -1))
    
    # rgb shape is now (1, target_width, 3)
    
    # Step 3: Encode to PNG
    png_bytes = encode_to_png(rgb)
    
    return png_bytes, target_width, 1
