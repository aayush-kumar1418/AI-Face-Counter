import cv2

print('cv2', cv2.__version__)
backends = [None, cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF]
for backend in backends:
    for idx in range(3):
        try:
            cap = cv2.VideoCapture(idx, backend) if backend is not None else cv2.VideoCapture(idx)
            ok = cap.isOpened()
            print('backend', backend, 'idx', idx, 'opened', ok)
            if ok:
                cap.release()
        except Exception as e:
            print('backend', backend, 'idx', idx, 'error', e)
