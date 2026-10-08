import os
import io
import urllib.parse
import boto3
from PIL import Image, ImageFilter, ImageOps

s3_client = boto3.client('s3')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET')

def generate_square(img, target_size=(1080, 1080)):
    # Clean center crop and resize to 1:1
    return ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)

def generate_story_with_blur(img, target_size=(1080, 1920)):
    # 9:16 Vertical canvas with blurred background padding
    target_w, target_h = target_size
    bg = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
    
    # Scale main image maintaining aspect ratio within canvas
    img_ratio = img.width / img.height
    canvas_ratio = target_w / target_h
    
    if img_ratio > canvas_ratio:
        new_w = target_w
        new_h = int(target_w / img_ratio)
    else:
        new_h = target_h
        new_w = int(target_h * img_ratio)
        
    main_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Paste centered
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    bg.paste(main_resized, (offset_x, offset_y))
    return bg

def generate_banner(img, target_size=(1200, 675)):
    # Clean crop and resize to 16:9
    return ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)

def save_and_upload(image, target_key):
    buffer = io.BytesIO()
    # Save optimized progressive JPEG
    image.convert('RGB').save(buffer, format='JPEG', quality=85, optimize=True)
    buffer.seek(0)
    s3_client.put_object(
        Bucket=OUTPUT_BUCKET,
        Key=target_key,
        Body=buffer,
        ContentType='image/jpeg'
    )
    print(f"Uploaded: s3://{OUTPUT_BUCKET}/{target_key}")

def lambda_handler(event, context):
    print("Received event:", event)
    for record in event.get('Records', []):
        src_bucket = record['s3']['bucket']['name']
        src_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        
        # Avoid processing non-image files
        file_ext = os.path.splitext(src_key)[1].lower()
        if file_ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            print(f"Skipping unsupported file format: {src_key}")
            continue
            
        base_filename = os.path.splitext(os.path.basename(src_key))[0]
        print(f"Processing asset: {src_key} from {src_bucket}")
        
        # Download raw image into memory
        response = s3_client.get_object(Bucket=src_bucket, Key=src_key)
        raw_bytes = response['Body'].read()
        
        with Image.open(io.BytesIO(raw_bytes)) as img:
            # 1. Square (1080x1080)
            sq_img = generate_square(img)
            save_and_upload(sq_img, f"processed/square/{base_filename}_square.jpg")
            
            # 2. Story (1080x1920) with blurred background
            story_img = generate_story_with_blur(img)
            save_and_upload(story_img, f"processed/stories/{base_filename}_story.jpg")
            
            # 3. Horizontal Banner (1200x675)
            banner_img = generate_banner(img)
            save_and_upload(banner_img, f"processed/banners/{base_filename}_banner.jpg")
            
    return {"statusCode": 200, "body": "Processing complete"}