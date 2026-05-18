import pyautogui
import time
import sys

print("=======================================")
print(" Mouse Coordinate Finder")
print("=======================================")
print("Move your mouse over the first image in Google Images.")
print("The coordinates will update below in real-time.")
print("Press Ctrl + C to exit when you're done.")
print("=======================================\n")

try:
    while True:
        x, y = pyautogui.position()
        positionStr = f'X: {str(x).rjust(4)} Y: {str(y).rjust(4)}'
        print(positionStr, end='')
        print('\b' * len(positionStr), end='', flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print('\n\nDone.')
    sys.exit()
