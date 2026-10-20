# ASTERA
### Your sky. Your story.

ASTERA is a small photo-editing app for night-sky pictures. Upload a JPG or PNG, adjust brightness and contrast, and use the threshold slider to find small bright regions. You can compare the original and edited photos, add a date and location, and download the result as a PNG.

[Open the app](https://astera-wilmarycmf.streamlit.app/)

## Features

- Brightness, contrast and detection threshold controls
- Original and processed photo previews
- Bright-point candidate count and optional circle markers
- Date and location stamp
- Final PNG and transparent light-layer downloads

The count is based on image brightness. A point could be a star, noise or another light source, so it is not a confirmed star count. Changing the threshold can split or merge bright regions. Up to 200 markers are shown.

## Image processing

- **Image arithmetic:** OpenCV addition, subtraction and multiplication change brightness and contrast. Values are clipped to the 0–255 range.
- **Thresholding:** the photo is converted to grayscale and blurred before applying a global threshold. Connected components find bright regions, with size and shape filters for the candidate count.
- **Drawing and annotation:** circles mark candidates. Pillow draws the date and location text, and OpenCV blends the stamp into the photo.
- **Alpha masks:** a softened threshold mask provides transparency for the light-layer PNG.

## Run locally

Use Python 3.11 or 3.12.

```sh
pip install -r requirements.txt
streamlit run app.py
```

## Files

- `app.py`: page layout and controls
- `core.py`: image processing and PNG export
- `test_app.py`: processing and interface checks
- `.streamlit/config.toml`: colors and upload limit

## Limits

Uploads must be JPG or PNG, up to 20 MB and 40 megapixels. Images are resized to fit within 2,000 × 2,000 pixels. The downloaded image matches the processed preview. The app works in memory during the session and has no photo archive. Exports do not include the original EXIF or GPS metadata.

## Tests

```sh
python test_app.py
```

The tests use a generated image with three bright spots. They check candidate detection, brightness clipping, watermark fitting, PNG transparency, invalid input and control changes. See `VALIDATION.md` for the test checklist.
