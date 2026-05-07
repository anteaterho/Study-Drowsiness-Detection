import cv2
img = cv2.imread(r'./assets/lama.jpg')
cv2.imshow('Window', img)
cv2.waitKey(0)
cv2.destroyAllWindows()