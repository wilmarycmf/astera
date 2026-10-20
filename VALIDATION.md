# Validation — October 19, 2026

- Reused app.py, core.py, requirements and theme from the original Astera_Streamlit_Ready_to_Deploy.zip.
- Automated Streamlit AppTest: initial page, injected PNG upload, brightness/contrast/threshold changes, highlight toggle, location entry, candidate count changes, both download controls, invalid-image error. Passed.
- Synthetic image: three separated bright disks detected as three candidates. Passed.
- Brightness/contrast clipping at 0 and 255. Passed.
- Annotation fitting: normal, narrow portrait, shallow panorama, 10×10 and 1×1. Passed. At extremely small sizes text is necessarily unreadable.
- RGBA export: transparent and opaque pixels preserved. Passed.
- Real browser: uploaded test_sky.png, entered San José, Puerto Rico, displayed original/processed and count 3, downloaded final PNG and transparent PNG. Passed.
- Downloaded files reopened using Pillow: RGB and RGBA, 900×600. Passed.
- Local Streamlit server starts and serves app. Passed.
- Public deployment: https://astera-wilmarycmf.streamlit.app/
- Anonymous HTTP page and health check returned 200, without login redirect.
- Cloud browser: uploaded PNG, verified count 3, location and highlight toggle; downloaded RGB final PNG and RGBA light layer. Passed.

Tested runtime: Python 3.9.6, Streamlit 1.50.0, OpenCV 4.14.0, NumPy 2.0.2, Pillow 11.3.0. Cloud should use Python 3.12.
