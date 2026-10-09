

# ⚡ Serverless Media Studio
### Scalable, Event-Driven Social Media Image Processing Engine on AWS

[![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-FF9900?style=for-the-badge&logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![Amazon S3](https://img.shields.io/badge/Amazon%20S3-569A31?style=for-the-badge&logo=amazons3&logoColor=white)](https://aws.amazon.com/s3/)
[![Amazon API Gateway](https://img.shields.io/badge/Amazon%20API%20Gateway-FF4F8B?style=for-the-badge&logo=amazonapigateway&logoColor=white)](https://aws.amazon.com/api-gateway/)
[![Python 3.12](https://img.shields.io/badge/Python%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

<p align="center">
  A high-throughput serverless media processing pipeline that eliminates server bottlenecks by streaming raw images directly to Amazon S3 via pre-signed URLs, asynchronously triggering AWS Lambda workers to generate standard social formats (Square, Story, Banner) in real time.
</p>

[Architecture](#-system-architecture) • [Key Features](#-key-features) • [Aspect Specifications](#-aspect-ratio-specifications) • [Tech Stack](#-tech-stack--infrastructure) • [Live Demo](#-live-dashboard)

</div>

---

## 📌 System Architecture

```text
┌──────────────┐
│  Web Client  │
└──────┬───────┘
       │ 1. POST / (filename, mime)
       ▼
┌───────────────────────────────┐
│ Amazon API Gateway (HTTP API) │
└──────────────┬────────────────┘
               │ 
               ▼
┌──────────────────────────────────────────────┐
│ AWS Lambda: SocialMediaPresignedSigner       │
│ ➔ Generates IAM-restricted Pre-Signed PUT URL│
└──────────────────────────────────────────────┘
       │
       │ 2. Direct PUT (Bypasses API payload limits)
       ▼
┌───────────────────────────────┐
│ Amazon S3: Raw Intake Bucket  │ ➔ (Auto-purges via Lifecycle Rules in 24 hrs)
└──────────────┬────────────────┘
               │
               │ 3. s3:ObjectCreated:* Event
               ▼
┌────────────────────────────────────────────── ┐
│ AWS Lambda: SocialMediaAspectResizer          │
│ ➔ 1024 MB RAM / Dedicated vCPU Execution     │
│ ➔ Multi-format matrix crop & blur via Pillow │
└──────────────┬────────────────────────────────┘
               │
               │ 4. Parallel Uploads (Square, Story, Banner)
               ▼
┌──────────────────────────────────────────────┐
│ Amazon S3: Processed Assets Bucket           │
└──────────────┬───────────────────────────────┘
               │
               │ 5. Polling & Visual Asset Delivery
               ▼
        ┌──────────────┐
        │  Web Client  │
        └──────────────┘


✨ Key Features
🚀 Direct-to-S3 Ingestion: Utilizes AWS Signature Version 4 Pre-Signed URLs to stream files straight to S3, bypassing API Gateway's 10 MB payload limits and avoiding proxy latency.

⚡ Decoupled Event-Driven Processing: Decouples upload from transformation via native s3:ObjectCreated:* triggers, providing high fault isolation and automated horizontal scaling.

🖼️ Intelligent Crop & Gaussian Fill: Rather than letterboxing with black bars, vertical stories apply dynamic aspect fitting backed by an underlying Gaussian-blurred plate.

🧹 Zero-Maintenance Storage Hygiene: S3 Object Lifecycle Management (ExpireRawUploads1Day) automatically purges intake files after 24 hours to prevent storage bloat.

🔒 Fine-Grained Least Privilege: Lambda execution roles and bucket policies are restricted to targeted resource ARNs without wildcard access permissions.



🛠️ Tech Stack & Infrastructure
Compute: AWS Lambda (Python 3.12 Runtime, Pillow image engine)

API Routing: Amazon API Gateway (HTTP API v2)

Object Storage: Amazon S3 (media-raw-intake-cyhakx & media-processed-assets-cyhakx)

Frontend Dashboard: Vanilla JavaScript, HTML5 Drag-and-Drop API, Tailwind CSS

Security & Networking: AWS IAM, S3 CORS Configuration, Resource-Based Lambda Policies


🌐 Live Dashboard
The static application is deployed on Amazon S3 website hosting:

Dashboard URL: http://media-processed-assets-cyhakx.s3-website.ap-south-1.amazonaws.com


📊 Performance & Optimization Notes
Memory-to-CPU Scaling: Resizing images at high resolution is CPU-bound. Configuring SocialMediaAspectResizer with 1024 MB RAM provides a dedicated vCPU core in Lambda, reducing latency to under 1 second.

Format Filtering: The client-side interface restricts inputs to standard MIME types (.jpg, .jpeg, .png, .webp), preventing decode errors from uncompiled formats like raw .heic.


