import sys
from time import time
import argparse
import numpy as np
import cv2
from libfaceid.detector import FaceDetectorModels, FaceDetector
from libfaceid.encoder  import FaceEncoderModels, FaceEncoder, FaceClassifierModels
from libfaceid.liveness import FaceLivenessDetectorModels, FaceLiveness



# Set the window name
WINDOW_NAME = "Facial Recognition"

# Set the input directories
INPUT_DIR_DATASET         = "datasets"
INPUT_DIR_MODEL_DETECTION = "models/detection/"
INPUT_DIR_MODEL_ENCODING  = "models/encoding/"
INPUT_DIR_MODEL_TRAINING  = "models/training/"
INPUT_DIR_MODEL           = "models/"

# Set width and height
RESOLUTION_QVGA   = (320, 240)
RESOLUTION_VGA    = (640, 480)
RESOLUTION_HD     = (1280, 720)
RESOLUTION_FULLHD = (1920, 1080)



def cam_init(width, height): 
    cap = cv2.VideoCapture(0)
    if sys.version_info < (3, 0):
        cap.set(cv2.cv.CV_CAP_PROP_FPS, 30)
        cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,  width)
        cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, height)
    else:
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap

def cam_release(cap):
    cap.release()
    cv2.destroyAllWindows()



def process_webcam(cam_resolution, out_resolution, framecount):

    # Initialize the camera
    cap = cam_init(cam_resolution[0], cam_resolution[1])

    # Initialize fps counter
    fps_frames = 0
    fps_start = time()

    while (True):
       
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret == 0:
            break
        
        # Resize to QVGA so that RPI we can have acceptable fps
        if out_resolution is not None:
            frame = cv2.resize(frame, out_resolution);
        
        # Display the resulting frame
        cv2.imshow(WINDOW_NAME, frame)

        # Update frame count
        fps_frames += 1
        if (framecount!=0 and fps_frames >= framecount):
            break

        # Check for user actions
        keyPressed = cv2.waitKey(1) & 0xFF
        if keyPressed == 27:
            break

    # Set the fps
    fps = fps_frames / (time() - fps_start)

    # Release the camera
    cam_release(cap)
    
    return fps


def process_facedetection(cam_resolution, out_resolution, framecount, model_detector=0):

    # Initialize the camera
    cap = cam_init(cam_resolution[0], cam_resolution[1])

    ###############################################################################
    # FACE DETECTION
    ###############################################################################
    # Initialize face detection
    face_detector = FaceDetector(model=model_detector, path=INPUT_DIR_MODEL_DETECTION, optimize=True)

    # Initialize fps counter
    fps_frames = 0
    fps_start = time()

    while (True):
       
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret == 0:
            break
        
        # Resize to QVGA so that RPI we can have acceptable fps
        if out_resolution is not None:
            frame = cv2.resize(frame, out_resolution);

        ###############################################################################
        # FACE DETECTION
        ###############################################################################
        # Detect faces and set bounding boxes
        faces = face_detector.detect(frame)
        for (index, face) in enumerate(faces):
            (x, y, w, h) = face
            cv2.rectangle(frame, (x,y), (x+w,y+h), (255,255,255), 1)

        # Display the resulting frame
        cv2.imshow(WINDOW_NAME, frame)

        # Update frame count
        fps_frames += 1
        if (framecount!=0 and fps_frames >= framecount):
            break

        # Check for user actions
        keyPressed = cv2.waitKey(1) & 0xFF
        if keyPressed == 27:
            break

    # Set the fps
    fps = fps_frames / (time() - fps_start)

    # Release the camera
    cam_release(cap)
    
    return fps


def save_video(saveVideo, out, resolution, filename):
    if saveVideo == True:
        print("video recording ended!")
        out.release()
        out = None
        saveVideo = False
    else:
        print("video recording started...")
        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        (h, w) = resolution
        out = cv2.VideoWriter(filename, fourcc, 12, (w, h))
        saveVideo = True
    return saveVideo, out

def set_text_and_boundingbox_on_face(frame, face_rect, face_id, confidence):
    (x, y, w, h) = face_rect
    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 1)
    cv2.putText(frame, "{} {:.2f}%".format(face_id, confidence), 
        (x+5,y+h-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


def process_facerecognition(cam_resolution, out_resolution, framecount, image=None, model_detector=0, model_recognizer=0):

    # Initialize the camera
    if image is not None:
        cap = cv2.VideoCapture(image)
    else:
        cap = cam_init(cam_resolution[0], cam_resolution[1])


    ###############################################################################
    # FACE DETECTION
    ###############################################################################
    # Initialize face detection
    face_detector = FaceDetector(model=model_detector, path=INPUT_DIR_MODEL_DETECTION, optimize=True)

    ###############################################################################
    # FACE RECOGNITION
    ###############################################################################
    # Initialize face recognizer
    face_encoder = FaceEncoder(model=model_recognizer, path=INPUT_DIR_MODEL_ENCODING, path_training=INPUT_DIR_MODEL_TRAINING, training=False)


    # Initialize fps counter
    fps_frames = 0
    fps_start = time()
    fps = 0
    saveVideo = False
    out = None
    
    while (True):
       
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret == 0:
            print("Unexpected error! " + image)
            break
        
        ###############################################################################
        # FACE DETECTION and FACE RECOGNITION
        ###############################################################################
        # Detect and recognize each face in the images

        # Resize to QVGA so that RPI we can have acceptable fps
        if out_resolution is not None:
            #frame = imutils.resize(frame, width=out_resolution[0])
            (h, w) = image.shape[:2]
            frame = cv2.resize(frame, (out_resolution[0], int(h * out_resolution[0] / float(w) )));

        ###############################################################################
        # FACE DETECTION
        ###############################################################################
        faces = face_detector.detect(frame)
        for (index, face) in enumerate(faces):
            (x, y, w, h) = face

            ###############################################################################
            # FACE RECOGNITION
            ###############################################################################
            face_id, confidence = face_encoder.identify(frame, (x, y, w, h))

            # Set bounding box and text
            set_text_and_boundingbox_on_face(frame, (x, y, w, h), face_id, confidence)


        # Update frame count
        fps_frames += 1
        if (framecount!=0 and fps_frames >= framecount):
            break
        if (fps_frames % 30 == 29):
            fps = fps_frames / (time() - fps_start)
            fps_frames = 0
            fps_start = time()
        cv2.putText(frame, "FPS {:.2f}".format(fps), 
            (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        # Save the frame to a video
        if saveVideo:
            out.write(frame)

        # Display the resulting frame
        cv2.imshow(WINDOW_NAME, frame)

        # Check for user actions
        keyPressed = cv2.waitKey(1) & 0xFF
        if keyPressed == 27: # ESC
            break
        elif keyPressed == 32: # Space
            saveVideo, out = save_video(saveVideo, out, frame.shape[:2], "facial_recognition_rpi3.avi")


    # Set the fps
    time_diff = time() - fps_start
    if time_diff:
        fps = fps_frames / time_diff

    if image is not None:
        cv2.waitKey(3000)

    if saveVideo == True:
        out.release()
    
    # Release the camera
    cam_release(cap)
    
    return fps


def process_facerecognition_livenessdetection(cam_resolution, out_resolution, framecount, image=None, model_detector=0, model_recognizer=0):

    # Initialize the camera
    if image is not None:
        cap = cv2.VideoCapture(image)
    else:
        cap = cam_init(cam_resolution[0], cam_resolution[1])


    ###############################################################################
    # FACE DETECTION
    ###############################################################################
    # Initialize face detection
    face_detector = FaceDetector(model=model_detector, path=INPUT_DIR_MODEL_DETECTION, optimize=True)

    ###############################################################################
    # FACE RECOGNITION
    ###############################################################################
    # Initialize face recognizer
    face_encoder = FaceEncoder(model=model_recognizer, path=INPUT_DIR_MODEL_ENCODING, path_training=INPUT_DIR_MODEL_TRAINING, training=False)


    ###############################################################################
    # EYE BLINKING DETECTOR
    ###############################################################################
    # Initialize detector for blinking eyes
    face_liveness = FaceLiveness(model=FaceLivenessDetectorModels.EYEBLINKING, path=INPUT_DIR_MODEL)
    face_liveness.initialize()
    eye_counter = 0
    total_eye_blinks = 0


    # Initialize fps counter
    fps_frames = 0
    fps_start = time()
    fps = 0
    saveVideo = False
    out = None
    
    while (True):
       
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret == 0:
            print("Unexpected error! " + image)
            break
        
        ###############################################################################
        # FACE DETECTION and FACE RECOGNITION
        ###############################################################################
        # Detect and recognize each face in the images
        
        # Resize to QVGA so that RPI we can have acceptable fps
        if out_resolution is not None:
            #frame = imutils.resize(frame, width=out_resolution[0])
            (h, w) = image.shape[:2]
            frame = cv2.resize(frame, (out_resolution[0], int(h * out_resolution[0] / float(w) )));
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_rgb = frame[:, :, ::-1]

        ###############################################################################
        # FACE DETECTION
        ###############################################################################
        faces = face_detector.detect(frame)
        for (index, face) in enumerate(faces):
            (x, y, w, h) = face

            ###############################################################################
            # FACE RECOGNITION
            ###############################################################################
            face_id, confidence = face_encoder.identify(frame, (x, y, w, h))

            # Set bounding box and text
            set_text_and_boundingbox_on_face(frame, (x, y, w, h), face_id, confidence)

            ###############################################################################
            # EYE BLINKING DETECTION
            ###############################################################################
            total_eye_blinks, eye_counter = face_liveness.detect(frame, (x, y, w, h), total_eye_blinks, eye_counter) 

        ###############################################################################
        # EYE BLINKING DETECTION
        ###############################################################################
        cv2.putText(frame, "Blinks: {}".format(total_eye_blinks), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        if len(faces) == 0:
            total_eye_blinks = 0


        # Update frame count
        fps_frames += 1
        if (framecount!=0 and fps_frames >= framecount):
            break
        if (fps_frames % 30 == 29):
            fps = fps_frames / (time() - fps_start)
            fps_frames = 0
            fps_start = time()
        cv2.putText(frame, "FPS {:.2f}".format(fps), (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        # Save the frame to a video
        if saveVideo:
            out.write(frame)

        # Display the resulting frame
        cv2.imshow(WINDOW_NAME, frame)

        # Check for user actions
        keyPressed = cv2.waitKey(1) & 0xFF
        if keyPressed == 27: # ESC
            break
        elif keyPressed == 32: # Space
            saveVideo, out = save_video(saveVideo, out, frame.shape[:2], "facial_recognition_rpi3.avi")


    # Set the fps
    time_diff = time() - fps_start
    if time_diff:
        fps = fps_frames / time_diff

    if image is not None:
        cv2.waitKey(3000)

    if saveVideo == True:
        out.release()
    
    # Release the camera
    cam_release(cap)
    
    return fps



def test_resolution_fps():
    
    resolutions = [ RESOLUTION_QVGA, RESOLUTION_VGA, RESOLUTION_HD, RESOLUTION_FULLHD ] #3.5-4FPS 7.5-8.25FPS, 22-23FPS
    frame_count = 100
  
    for resolution in resolutions:
        fps = process_webcam( resolution, None, frame_count )
        print( "resolution = {}x{}\tfps = {:.2f}".format(resolution[0], resolution[1], fps) )

def test_detection_fps():
    
    frame_count = 100
    for i in range(len(FaceDetectorModels)):
        fps = process_facedetection( RESOLUTION_QVGA, None, frame_count, model_detector = i )
        print( "MODEL = {}\tfps = {:.2f}".format(i, fps) )

def test_recognition_fps():
    
    frame_count = 100
    for i in range(len(FaceDetectorModels)):
        for j in range(len(FaceEncoderModels)):
            fps = process_facerecognition( RESOLUTION_QVGA, None, 0, model_detector=i, model_recognizer=j)
            print( "MODEL = {}x{}\tfps = {:.2f}".format(i, j, fps) )

def test():

    # check webcam speed
    test_resolution_fps()

    # check face detection
    test_detection_fps()

    # check face recognition
    test_recognition_fps()

def train_recognition(model_detector, model_encoder, verify):

    face_detector = FaceDetector(model=model_detector, path=INPUT_DIR_MODEL_DETECTION)
    face_encoder = FaceEncoder(model=model_encoder, path=INPUT_DIR_MODEL_ENCODING, path_training=INPUT_DIR_MODEL_TRAINING, training=True)
    face_encoder.train(face_detector, path_dataset=INPUT_DIR_DATASET, verify=verify, classifier=FaceClassifierModels.GAUSSIAN_NB)


def run():
    # set models to use
#    detector=FaceDetectorModels.HAARCASCADE
#    detector=FaceDetectorModels.DLIBHOG
#    detector=FaceDetectorModels.DLIBCNN
#    detector=FaceDetectorModels.SSDRESNET
    detector=FaceDetectorModels.MTCNN

    encoder=FaceEncoderModels.LBPH
#    encoder=FaceEncoderModels.OPENFACE
#    encoder=FaceEncoderModels.DLIBRESNET

    # train the models based on selected models
    train_recognition(detector, encoder, True)

    # check face recognition
    #fps = process_facedetection( RESOLUTION_QVGA, None, 0, model_detector=detector )
    fps = process_facerecognition( RESOLUTION_QVGA, None, 0, model_detector=detector, model_recognizer=encoder)
    #fps = process_facerecognition_livenessdetection( RESOLUTION_QVGA, None, 0, model_detector=detector, model_recognizer=encoder)
    print( "resolution = {}x{}\tfps = {:.2f}".format(RESOLUTION_QVGA[0], RESOLUTION_QVGA[1], fps) )


def main(args):
    if sys.version_info < (3, 0):
        print("Error: Python2 is slow. Use Python3 for max performance.")
        return
    if args.detector and args.encoder:
        try:
            detector = FaceDetectorModels(int(args.detector))
            encoder = FaceEncoderModels(int(args.encoder))
            print( "Parameters: {} {}".format(detector, encoder) )
            train_recognition(detector, encoder, True)
            fps = process_facerecognition( RESOLUTION_QVGA, None, 0, model_detector=detector, model_recognizer=encoder)
            print( "Result: {}x{} {:.2f} fps".format(RESOLUTION_QVGA[0], RESOLUTION_QVGA[1], fps) )
        except:
            print( "Invalid parameter" )
        return
    run()

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--detector', required=False,
        help='Detector model to use.\nOptions: 0-HAARCASCADE, 1-DLIBHOG, 2-DLIBCNN, 3-SSDRESNET, 4-MTCNN.')
    parser.add_argument('--encoder', required=False,
        help='Encoder model to use.\nOptions: 0-LBPH, 1-OPENFACE, 2-DLIBRESNET.')
    return parser.parse_args(argv)

if __name__ == '__main__':
    main(parse_arguments(sys.argv[1:]))
