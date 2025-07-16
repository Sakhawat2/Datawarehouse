import mimetypes

file_path = "storage/videos/Test.mp4"
mime_type, _ = mimetypes.guess_type(file_path)
print(f"MIME type: {mime_type}")
