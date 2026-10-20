from datetime import date
from io import BytesIO
from unittest.mock import patch
import numpy as np
import cv2
from PIL import Image
from streamlit.testing.v1 import AppTest
from core import *
photo=np.full((600,900,3),12,dtype=np.uint8)
for x,y,r in [(100,100,3),(300,200,4),(700,150,5)]: cv2.circle(photo,(x,y),r,(255,255,255),-1)
raw=png_bytes(photo)
assert np.array_equal(load_photo(raw),photo)
assert enhance(photo,90,1.7).max()==255
assert enhance(photo,-70,.7).min()==0
assert len(detect_highlights(photo,180).points)==3
for h,w in [(600,900),(40,1800),(1800,40),(10,10),(1,1)]:
 src=np.full((h,w,3),100,np.uint8); out=annotate(src,date(2026,10,19),'San José, Puerto Rico',3,[],True)
 assert out.shape==src.shape and np.any(out!=src)
rgba=transparent_light_layer(photo,detect_highlights(photo,180).mask)
assert Image.open(BytesIO(png_bytes(rgba))).mode=='RGBA'
assert rgba[:,:,3].min()==0 and rgba[:,:,3].max()==255
for data in [b'bad',b'']:
 try: load_photo(data); raise AssertionError('Invalid accepted')
 except ValueError: pass
at=AppTest.from_file('app.py').run(); assert not at.exception
class Upload:
 def getvalue(self): return raw
with patch('streamlit.file_uploader',return_value=Upload()):
 at=AppTest.from_file('app.py').run(); assert not at.exception
 assert at.metric[0].value=='3'
 at.slider[0].set_value(-70); at.slider[1].set_value(.7); at.slider[2].set_value(250)
 at.toggle[0].set_value(True); at.text_input[0].set_value('San José, Puerto Rico')
 at.run(); assert not at.exception and at.metric[0].value=='0'
 assert len(at.get('download_button'))==2
 at.slider[0].set_value(90); at.slider[1].set_value(1.7); at.slider[2].set_value(100)
 at.run(); assert not at.exception
with patch('streamlit.file_uploader',return_value=type('Bad',(),{'getvalue':lambda _:b'bad'})()):
 at=AppTest.from_file('app.py').run(); assert not at.exception and len(at.error)==1
print('All checks passed.')
