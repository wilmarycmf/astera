# ASTERA — Your sky. Your story.

A minimalist night-sky photo generator for Part 3. Upload JPG/PNG, adjust brightness and contrast, choose a detection threshold, compare original and processed images, add a date and place, and download the finished PNG. Optional candidate markers and a transparent light-layer PNG are included.

## Run

Python 3.11 or 3.12 recommended.

```sh
pip install -r requirements.txt
streamlit run app.py
```

## Concepts

- **Image arithmetic:** saturated OpenCV addition/subtraction and multiplication adjust brightness and contrast without integer wraparound.
- **Thresholding:** grayscale, Gaussian blur, global threshold, morphological opening and connected components locate small bright regions. Area/aspect filters exclude some large or elongated regions.
- **Drawing / annotation:** OpenCV circles mark candidates; a fitted date/location stamp uses Pillow text for accented place names and OpenCV blending.
- **Alpha masks:** the optional RGBA export uses the softened threshold mask as alpha. It includes thresholded regions, not just counted candidates.

Candidates may be noise, lamps, stars or other objects. ASTERA does not confirm or identify stars. Counts need not decrease monotonically as the threshold rises: regions can split or merge. At most 200 candidate circles are drawn.

Images are limited to 20 MB / 40 megapixels and fitted within 2,000 pixels on each side. Download dimensions match the processed preview. Uploaded images and edits are processed in memory for the active session; there is no database, account system or photo archive. Downloaded PNGs do not preserve original EXIF/GPS metadata. Nothing is written to a photo gallery on the server.

## Publish to Streamlit Community Cloud

1. Create a GitHub repository and upload this folder's contents at the repository root, including `.streamlit/config.toml`.
2. Sign in at https://share.streamlit.io and choose Create app, selecting the repository, branch `main` and entrypoint `app.py`.
3. Choose Python 3.12 in advanced settings, then deploy.
4. Confirm app access is public. Open its actual `.streamlit.app` URL without a signed-in session and test uploading/downloading before submitting it.

**Deployment status:** not yet published; awaiting the user's GitHub sign-in. No public URL has been verified.

## Validation

Run `python test_app.py` from this folder. Tests cover processing, clipping, known synthetic candidate counts, small/panoramic watermark fitting, RGB/RGBA export, invalid input, and Streamlit control changes. Browser checks also uploaded a synthetic image and downloaded both PNG exports successfully. See VALIDATION.md.
