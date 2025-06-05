import os
import shutil
from pprint import pprint
new_dir = r"C:\Users\User\Downloads\New folder\Fallout 4 Creation Club"
# Alternatively: new_dir = "C:\\Users\\User\\Downloads\\New folder\\Fallout 4 Creation Club"

os.chdir(new_dir)
cur_dir = os.getcwd()
folders = [f for f in os.listdir() if os.path.isdir(f)]
for folder in folders:
    items = os.listdir(folder)
    print(items)
    for item in items:
        shutil.move(f"{folder}/{item}", "./")
# pprint(os.getcwd())