import numpy as np
import cv2
from PIL import Image


def blur_background_pil(img: Image.Image, blur_kernel=15):
    img_np = np.array(img)

    # Convert to grayscale and detect edges
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 30, 100)

    # Find contours and fill them to create a mask
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    leaf_mask = np.zeros_like(gray, dtype=np.uint8)
    cv2.drawContours(leaf_mask, contours, -1, 255, thickness=cv2.FILLED)

    # Smooth and dilate the mask a bit
    leaf_mask = cv2.dilate(leaf_mask, np.ones((5, 5), np.uint8), iterations=1)
    mask_bool = leaf_mask.astype(bool)

    # Apply Gaussian blur to full image
    blurred_img = cv2.GaussianBlur(img_np, (blur_kernel, blur_kernel), 0)

    # Combine: keep leaf unblurred, blur rest
    final_img = blurred_img.copy()
    final_img[mask_bool] = img_np[mask_bool]

    return Image.fromarray(final_img)
