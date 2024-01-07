import sys
import re
from pathlib import Path
import shutil
from eyed3.id3 import Tag
import eyed3
from typing import NamedTuple
from functools import lru_cache
from collections import defaultdict


class File(NamedTuple):
    path: Path

    @property
    @lru_cache()
    def length_ms(self):
        audio_file = eyed3.load(self.path)  
        return int(audio_file.info.time_secs * 1_000)
    
    @property
    @lru_cache()
    def name(self):
        return self.path.name

    def append_to(self, target):
        with self.path.open("rb") as fin:
            shutil.copyfileobj(fin, target)


def main(path: str, pattern: str):
    path = Path(path)
    files = sorted(
        File(path=f) for f in path.glob("*")
        if re.match(pattern, f.name)
    )

    grouped = defaultdict(lambda: [])
    for f in files:
        m = re.search("\d+-\d+ (.+?)(\s*\(.+|mp3)", f.name)
        chapter_title = m.group(1).strip(".'")
        grouped[chapter_title].append(f)

    fout_path = Path(f"{path.name}.mp3")

    with fout_path.open("wb") as fout:
        for f in files:
            f.append_to(fout)

    total_length = sum(f.length_ms for f in files)
    print(total_length)

    tag = eyed3.load(fout_path).tag

    tag.title = path.name
    tag.setTextFrame(b"TLEN", str(total_length))
    time = 0
    index = 0
    element_ids = []
    for idx, (chapter, chapter_files) in enumerate(grouped.items()):
        print(f"processing chapter {chapter}")
        element_id = f"ch{idx}".encode()
        chapter_length = sum(f.length_ms for f in chapter_files)
        new_chapter = tag.chapters.set(element_id, (time, time + chapter_length))
        new_chapter.sub_frames.setTextFrame(b"TIT2", chapter)
        time += chapter_length
        element_ids.append(element_id)
    tag.table_of_contents.set(b"toc", child_ids=element_ids)
    tag.save()






    
    


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
