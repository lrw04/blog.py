from datetime import timedelta, datetime
from rjsmin import jsmin
from rcssmin import cssmin
from bs4 import BeautifulSoup
from pathlib import Path
from email.utils import format_datetime
import subprocess
import shutil
import yaml
import json
import sys
import logging
import multiprocessing
import http.server
import time
import operator
from xml.sax.saxutils import escape as xml_escape

ENC = "utf-8"
GEN = "blog.py by lrw04"
logging.basicConfig(
    format="%(asctime)s [%(levelname)s]: %(message)s", level=logging.WARNING
)


def dict_combine(*args):
    ans = {}
    for d in args:
        for k in d:
            ans[k] = d[k]
    return ans


def peek_document(html, maxl):
    dom = BeautifulSoup(html, "html.parser")
    exc = ""
    for elem in dom.find_all(["p", "li"]):
        exc += elem.decode_contents()[:maxl] + " "
        maxl -= len(elem.decode_contents())
        if maxl < 0:
            break
    return exc + "..."


class Document:
    def __init__(self, p: Path, fmt: str, deltat: timedelta):
        logging.info(f"Parsing document {p}")
        self.path = p
        self.peek = None
        assert p.suffix == ".md"
        with open(p, encoding=ENC) as f:
            meta = next(yaml.safe_load_all(f))
        self.meta = dict_combine({"visible": True}, meta)
        self.ts = datetime.strptime(self.meta["modification"], fmt)
        self.meta["modification"] = (self.ts + deltat).timestamp()
        self.shown = (
            "hidden_until" not in self.meta
            or datetime.strptime(self.meta["hidden_until"], fmt) + deltat
            < datetime.now()
        )

    def generate_peek(self, p: Path, l: int):
        self.peek = peek_document(p.open(encoding=ENC).read(), l)

    def index(self) -> dict:
        return dict_combine({"peek": self.peek}, self.meta)

    def entry(self, d: str, p: list) -> list:
        if not self.shown:
            return []
        return [
            {
                "title": self.meta["title"],
                "link": "https://" + d + "/" + "/".join(p) + ".html",
                "desc": self.peek,
                "tstr": format_datetime(self.ts),
                "ts": self.ts,
                "id": "/".join(p),
            }
        ]


class Category:
    def __init__(self, p: Path, fmt: str, deltat: timedelta):
        logging.info(f"Parsing category {p}")
        self.subcategories = {}
        self.documents = {}
        self.path = p
        with (p / "config.yaml").open(encoding=ENC) as f:
            self.config = dict_combine(
                {"listed": True, "brief": False}, yaml.safe_load(f)
            )
        for sc in p.iterdir():
            if sc.parts[-1][0] == ".":
                continue
            if sc.is_dir():
                try:
                    self.subcategories[sc.stem] = Category(sc, fmt, deltat)
                except Exception:
                    logging.warning(f"Ignoring subcategory {sc} with invalid config")
            elif sc.suffix == ".md":
                try:
                    self.documents[sc.stem] = Document(sc, fmt, deltat)
                    if not self.documents[sc.stem].shown:
                        self.documents.pop(sc.stem)
                except Exception:
                    logging.warning(f"Ignoring document {sc} with invalid format")

    def build_hierarchy(self, p: Path, tem: Path):
        logging.info(f"Building hierarchy for {p}")
        shutil.copy(tem / "index.html", p / "index.html")
        for sc in self.subcategories:
            (p / sc).mkdir()
            self.subcategories[sc].build_hierarchy(p / sc, tem)
        for d in self.documents:
            shutil.copy(tem / "document.html", p / (d + ".html"))

    def build_blob_hierarchy(self, p: Path):
        for sc in self.subcategories:
            (p / sc).mkdir()
            self.subcategories[sc].build_blob_hierarchy(p / sc)
        if self.config["brief"]:
            shutil.copy(self.path / "brief.html", p / "brief.html")

    def get_jobs(self, blob: Path) -> list[tuple[Path, Path]]:
        ans = []
        for sc in self.subcategories:
            ans += self.subcategories[sc].get_jobs(blob / sc)
        for d in self.documents:
            ans.append((self.documents[d].path, blob / (d + ".html")))
        return ans

    def generate_peek(self, b: Path, l: int):
        for sc in self.subcategories:
            self.subcategories[sc].generate_peek(b / sc, l)
        for d in self.documents:
            self.documents[d].generate_peek(b / (d + ".html"), l)

    def index(self) -> dict:
        ans = self.config.copy()
        ans["subcategories"] = {}
        ans["documents"] = {}
        for sc in self.subcategories:
            ans["subcategories"][sc] = self.subcategories[sc].index()
        for d in self.documents:
            ans["documents"][d] = self.documents[d].index()
        return ans

    def entry(self, d: str, p: list) -> list:
        ans = []
        for sc in self.subcategories:
            ans += self.subcategories[sc].entry(d, p + [sc])
        for e in self.documents:
            ans += self.documents[e].entry(d, p + [e])
        return ans


def rss_item(entry):
    return """        <item>
            <title>{title}</title>
            <link>{link}</link>
            <description>{desc}</description>
            <pubDate>{tstr}</pubDate>
            <guid>{guid}</guid>
        </item>
""".format(
        title=entry["title"],
        link=entry["link"],
        desc=xml_escape(entry["desc"]),
        tstr=entry["tstr"],
        guid=entry["link"],
    )


class Repository:
    def __init__(self, root: Path):
        self.root = root
        self.parse()

    def parse(self):
        logging.info("Started parsing")
        try:
            with (self.root / "config.yaml").open(encoding=ENC) as f:
                self.config = yaml.safe_load(f)
        except Exception:
            logging.critical(f"Config parsing failed")
            exit(-1)
        self.ts_delta = (
            datetime.utcnow()
            - datetime.now()
            + timedelta(seconds=self.config["timezone"] * 3600)
        )
        try:
            self.tree = Category(
                self.root / "documents", self.config["datetime_format"], self.ts_delta
            )
        except:
            logging.critical(f"Config parsing failed")
            exit(-1)

    def build(self):
        logging.info("Started build")
        artifact_root = self.root / self.config["artifacts_dir"]
        shutil.rmtree(artifact_root, ignore_errors=True)
        artifact_root.mkdir()

        blob_root = artifact_root / "blob"
        blob_root.mkdir()
        shutil.copytree(self.root / "static", artifact_root / "static")

        self.tree.build_hierarchy(artifact_root, self.root / "templates")
        self.tree.build_blob_hierarchy(blob_root)
        jobs = self.tree.get_jobs(blob_root)
        self.convert_all(jobs, self.config["pandoc_args"])

        self.tree.generate_peek(blob_root, self.config["peek_length"])
        with (blob_root / "index.json").open("w", encoding=ENC) as f:
            json.dump(self.tree.index(), f, sort_keys=True)
            f.write("\n")
        for f in (artifact_root / "static").iterdir():
            if f.suffix == ".js":
                with f.open(encoding=ENC) as fin:
                    cont = fin.read()
                with f.open("w", encoding=ENC) as fout:
                    fout.write(jsmin(cont))
                    fout.write("\n")
            elif f.suffix == ".css":
                with f.open(encoding=ENC) as fin:
                    cont = fin.read()
                with f.open("w", encoding=ENC) as fout:
                    fout.write(cssmin(cont))
                    fout.write("\n")
        with (artifact_root / "rss.xml").open("w", encoding=ENC) as f:
            f.write(self.rss())

    def convert_all(self, jobs: list[tuple[Path, Path]], args: list[str]):
        cmds = [["pandoc", str(q[0]), "-o", str(q[1])] + args for q in jobs]
        with multiprocessing.Pool() as p:
            p.map(subprocess.run, cmds)

    def serve(self):
        subprocess.run(
            [
                "python",
                "-m",
                "http.server",
                "-d",
                str(self.root / self.config["artifacts_dir"]),
            ]
        )

    def rss(self):
        entries = sorted(
            self.tree.entry(self.config["rss"]["domain"], []),
            key=operator.itemgetter("ts"),
        )
        return """<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>{title}</title>
        <link>{link}</link>
        <description>{desc}</description>
        <language>{lang}</language>
        <generator>{gen}</generator>
        <atom:link href="{href}" rel="self" type="application/rss+xml" />
{items}
    </channel>
</rss>
""".format(
            title=self.tree.config["title"],
            link="https://" + self.config["rss"]["domain"] + "/",
            desc=self.config["rss"]["desc"],
            lang=self.config["rss"]["lang"],
            gen=GEN,
            items="".join([rss_item(k) for k in entries]),
            href="https://" + self.config["rss"]["domain"] + "/rss.xml",
        )


def main():
    t0 = time.thread_time()
    try:
        op = sys.argv[1]
        assert len(sys.argv) <= 3
    except IndexError:
        print("Error: operation not specified: can be `build' or `serve'.")
        exit(-1)
    except AssertionError:
        print("Error: too many arguments specified.")
        exit(-1)
    if op not in ["build", "serve"]:
        print("Error: invalid operation, should be `build' or `serve'.")
        exit(-1)
    p = "." if len(sys.argv) < 3 else sys.argv[2]
    repo = Repository(Path(p))
    t1 = time.thread_time()
    if op == "build":
        repo.build()
        t2 = time.thread_time()
        logging.info(f"Parsing lasted {t1 - t0} s, building lasted {t2 - t1} s")
    elif op == "serve":
        repo.serve()


if __name__ == "__main__":
    main()
