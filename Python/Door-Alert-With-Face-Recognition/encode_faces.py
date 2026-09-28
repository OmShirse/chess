"""
Encode Faces — Build the face recognition database
====================================================
Scans images in --dataset directory, computes face encodings,
and saves them to --encodings pickle file.

Dataset structure:
    dataset/
        Alice/
            photo1.jpg
            photo2.jpg
        Bob/
            photo1.jpg

Usage:
    python encode_faces.py --dataset dataset/ --encodings encodings.pickle
"""

import face_recognition
import pickle
import cv2
import os
import argparse
from imutils import paths


def parse_args():
    ap = argparse.ArgumentParser(description="Encode known faces")
    ap.add_argument("-i", "--dataset",   required=True, help="path to dataset directory")
    ap.add_argument("-e", "--encodings", required=True, help="path to output encodings pickle")
    ap.add_argument("-d", "--detection", default="hog",  choices=["hog", "cnn"],
                    help="face detection model (hog=CPU, cnn=GPU)")
    return ap.parse_args()


def main():
    args        = parse_args()
    image_paths = list(paths.list_images(args.dataset))

    known_encodings = []
    known_names     = []

    for i, image_path in enumerate(image_paths):
        name  = image_path.split(os.sep)[-2]  # parent folder = person name
        print(f"[INFO] Processing {i+1}/{len(image_paths)}: {name}")

        image   = cv2.imread(image_path)
        rgb     = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        boxes   = face_recognition.face_locations(rgb, model=args.detection)
        encs    = face_recognition.face_encodings(rgb, boxes)

        for enc in encs:
            known_encodings.append(enc)
            known_names.append(name)

    print(f"[INFO] Saving {len(known_encodings)} encoding(s) to {args.encodings}")
    data = {"encodings": known_encodings, "names": known_names}
    with open(args.encodings, "wb") as f:
        f.write(pickle.dumps(data))
    print("[INFO] Done.")


if __name__ == "__main__":
    main()
