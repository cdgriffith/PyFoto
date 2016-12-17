import os

from pyfoto.organizer import Organize

loc = "//192.168.0.6/drive_e/albums/"

o = Organize()

for dir in os.listdir(loc):
    path = loc + dir
    with open(path + "/index.txt") as f:
        info = f.readlines()
    assert "Tags" in info[4]
    tags = []
    for tag in info[5:]:
        if not tag.startswith("  "):
            break
        tag = tag.strip().lower().replace(" ", "-").replace(".", "-").strip("-")
        if tag:
            tags.append(tag)
    print(tags)
    print(dir)
    o.add_images(path, tags=tags)
