import cv2

# Open webcam
cap = cv2.VideoCapture(0)

# Set resolution (optional)
cap.set(3, 640)
cap.set(4, 480)

# Define video codec and output file
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('webcam_video.mp4', fourcc, 20.0, (640, 480))

print("🎬 Recording... Press 'q' to stop.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break
    out.write(frame)
    cv2.imshow('Webcam Feed', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()
print("✅ Saved as webcam_video.mp4")
