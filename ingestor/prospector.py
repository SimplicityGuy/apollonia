"""
Creates the Prospector class for discovering file attributes.

Classes:
    Prospector
"""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from xxhash import xxh128


class Prospector:
    """
    Prospector class provides a way to get some basic information about a file and
    related files. Related files can be seen as external metadata about the original
    file.

    Methods:
        prospect(): Collect all the information of the file specified by the path that
        is used elsewhere in apollonia.
    """

    def __init__(self, path: Path):
        """
        Initialization of the Prospector class.

        Args:
            path (Path): The file object specified as a Path.

        Returns:
            Prospector: Instance of the class.
        """
        self.path: Path = path

    def prospect(self) -> dict[str, Any]:
        """
        Collect all the information of the file specified by the path that is used
        elsewhere in apollonia.

        Returns:
            dict[str, Any]: Dictionary of the data collected.
        """
        filename: str = str(self.path)
        print(f" --: prospecting {filename} :-- ")

        data: dict = {
            "found_at": datetime.utcnow().timestamp(),
            "name": filename,
            "hashes": self.__hashes(),
            "neighbors": self.__neighbors(),
        }

        return data

    def __hashes(self) -> dict[str, str]:
        """
        Computes hashes of the file specified by the path.

        Returns:
            dict[str, str]: Dictionary of the hashes of the file, there the key
            specifies the type of hash.
        """
        hash_sha256 = sha256()
        hash_xxh128 = xxh128()

        with self.path.open("rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                hash_sha256.update(byte_block)
                hash_xxh128.update(byte_block)

        return {"sha256": hash_sha256.hexdigest(), "xxh128": hash_xxh128.hexdigest()}

    def __neighbors(self) -> list[str]:
        """
        Looks for other files with similar naming to the file specified by the path.
        These may be, perhaps, one or more of the following: cue, m3u, txt, or other
        files, such as tracklist.txt.

        Returns:
            list[str]: Neighboring files.
        """

        limit: int = 3
        start: int = limit if len(self.path.stem) > limit else 0
        search_stems: list[str] = [self.path.stem[start:], "[t|T]racklist", "[t|T]racks"]
        data: list[str] = []
        for search_stem in search_stems:
            data += [
                str(filename)
                for filename in self.path.glob(f"**/*{search_stem}*")
                if filename != str(self.path)
            ]

        return data
