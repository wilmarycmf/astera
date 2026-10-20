# Testing

## Processing checks

- Three separate bright spots return three candidates.
- Brightness and contrast stay within the 0–255 range.
- The stamp fits landscape, portrait and panoramic images.
- Very small images process without an error, although their text may be unreadable.
- Final PNGs open as RGB images.
- Light-layer PNGs open as RGBA images with transparent areas.
- Invalid uploads show an error message.

## Interface checks

- Brightness, contrast and threshold controls update the result.
- The marker switch and location field work.
- Both download buttons produce PNG files.
- The public app opens in an incognito window without signing in.

## Run the checks

```sh
python test_app.py
```

[Live app](https://astera-wilmarycmf.streamlit.app/)
