docker-compose up -d 

python3 app.py

markdown

## opc-ocr

python3 ocr.py --batch --output out.a ../images/

usage: ocr.py [-h] [--debug] [--visualize] image_path

Extract card information using targeted OCR

positional arguments:
  image_path   Path to the card image

options:
  -h, --help   show this help message and exit
  --debug      Print all detected text
  --visualize  Create visualization of regions
