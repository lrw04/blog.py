from datetime import datetime
from pathlib import Path
import dateutil.parser
import subprocess
import argparse
import shutil
import yaml
import json
import sys
from rjsmin import jsmin
from rcssmin import cssmin
from bs4 import BeautifulSoup


class BlogpyRepo:
    def __init__(self, root: Path):
        self.root = root
        self.document_dir = root / "documents"
        self.templates_dir = root / "templates"
        with (root / "config.yaml").open(encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.docs = self.parse_dir(self.document_dir)

    def parse_dir(self, path: Path) -> dict:
        sub = {
            "subdirs": {},
            "documents": {},
        }
        for sc in path.iterdir():
            if sc.parts[-1][0] == ".":
                continue
            if sc.is_dir():
                sub["subdirs"][sc.stem] = self.parse_dir(sc)
            elif sc.suffix == ".md":
                sub["documents"][sc.stem] = self.parse_doc(sc)
        with (path / "config.yaml").open(encoding="utf-8") as f:
            return {"listed": True, "brief": False} | yaml.safe_load(f) | sub

    def parse_doc(self, path: Path) -> dict:
        with path.open(encoding="utf-8") as f:
            meta = next(yaml.safe_load_all(f))
            return (
                {"visible": True}
                | meta
                | {
                    "modification": datetime.strptime(
                        meta["modification"], self.config["datetime_format"]
                    ).timestamp(),
                }
            )

    def generate(self):
        self.artifacts_dir = self.root / self.config["artifacts_dir"]
        shutil.rmtree(self.artifacts_dir, ignore_errors=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.blob_dir = self.artifacts_dir / "blob"
        self.blob_dir.mkdir(exist_ok=True)
        shutil.copytree(
            self.root / "static", self.artifacts_dir / "static", dirs_exist_ok=True
        )
        self.generate_blob(Path("."), self.docs)
        self.generate_hierarchy(Path("."), self.docs)
        for x in (self.artifacts_dir / "static").iterdir():
            if x.suffix == ".js":
                self.minify_js(x)
            elif x.suffix == ".css":
                self.minify_css(x)
        self.peek_content(self.docs, self.document_dir, self.blob_dir)
        with (self.blob_dir / "index.json").open("w", encoding="utf-8") as f:
            f.write(json.dumps(self.docs))

    def peek_content(self, index, docdir, blobdir):
        for subdir in index["subdirs"]:
            self.peek_content(
                index["subdirs"][subdir], docdir / subdir, blobdir / subdir
            )
        for document in index["documents"]:
            index["documents"][document]["peek"] = (
                BeautifulSoup(
                    (blobdir / (document + ".content.html"))
                    .open(encoding="utf-8")
                    .read(),
                    "html.parser",
                )
                .get_text()[:150]
                .replace("\n", " ")
                + "..."
            )

    def md2html(self, in_f, out_f):
        subprocess.run(
            ["pandoc", str(in_f), "-o", str(out_f)] + self.config["pandoc_args"]
        )

    def generate_blob(self, path, material):
        print("blob:", path)
        (self.blob_dir / path).mkdir(exist_ok=True)
        if material["brief"]:
            shutil.copy(
                self.document_dir / path / "brief.html",
                self.blob_dir / path / "brief.html",
            )
        for post in material["documents"]:
            self.md2html(
                self.document_dir / path / (post + ".md"),
                self.blob_dir / path / (post + ".content.html"),
            )
        for subdir in material["subdirs"]:
            self.generate_blob(path / subdir, material["subdirs"][subdir])

    def generate_hierarchy(self, path, material):
        print("hierarchy:", path)
        (self.artifacts_dir / path).mkdir(exist_ok=True)
        shutil.copy(
            self.templates_dir / "index.html", self.artifacts_dir / path / "index.html"
        )
        for post in material["documents"]:
            shutil.copy(
                self.templates_dir / "document.html",
                self.artifacts_dir / path / (post + ".html"),
            )
        for subdir in material["subdirs"]:
            self.generate_hierarchy(path / subdir, material["subdirs"][subdir])

    def minify_js(self, fn):
        with fn.open(encoding="utf-8") as f:
            cont = f.read()
        with fn.open("w", encoding="utf-8") as f:
            f.write(jsmin(cont))

    def minify_css(self, fn):
        with fn.open(encoding="utf-8") as f:
            cont = f.read()
        with fn.open("w", encoding="utf-8") as f:
            f.write(cssmin(cont))


def main():
    parser = argparse.ArgumentParser(description="Compile a blog.py repository.")
    parser.add_argument(
        "--root", nargs="?", type=Path, const=Path("."), default=Path(".")
    )
    args = parser.parse_args()
    BlogpyRepo(args.root).generate()


if __name__ == "__main__":
    main()
