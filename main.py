import itertools
import os
import math
from datetime import datetime
from multiprocessing.dummy import Pool as ThreadPool
from collections import namedtuple

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader("html"), autoescape=select_autoescape())
Options = namedtuple(
    "Options",
    ("base_folder", "all_posts", "root_path", "switch_message", "switch_path"),
)


def take(n, it):
    """
    Return first n items of the iterable as a list
    """
    it = iter(it)
    while r := list(itertools.islice(it, n)):
        yield r


def get_paintings(artist_id):
    """
    Fetch artist last painting from their gallery
    """
    url = "https://www.dailypaintworks.com/Home/SearchPostsResults"
    payload = {
        "inSearchId": "1680581114640",
        "inSitePage": "GALLERY",
        "inByDate": "false",
        "inCurrentDate": datetime.now().strftime("%M/%D/%Y"),
        "inPageNumber": "0",
        "inDisplayedPostCount": "0",
        "isInArrangeMode": "false",
        "inArtistId": str(artist_id),
    }
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    res = requests.request("POST", url, headers=headers, data=payload)
    assert res.status_code == 200, res.text
    return res.json()


def sync():
    aids = os.getenv("ARTIST_IDS")
    if not aids:
        print("No artist ids found. Exiting")
        return

    aids = aids.split(",")
    print("[%d] artist ids found" % len(aids))

    pool = ThreadPool(4)
    data = pool.map(get_paintings, aids)
    pool.close()
    pool.join()

    data = sorted(
        sum([d["Posts"] for d in data], []),
        key=lambda p: (
            datetime.strptime(p["DateString"], "%b %d, %Y"),
            p["GalleryName"],
        ),
        reverse=True,
    )
    return data


def update_template(all_posts, page_size=120):
    if not all_posts:
        return

    options = [
        Options("docs", all_posts, "/", "Show only available", "/available"),
        Options(
            os.path.join("docs", "available"),
            [p for p in all_posts if not p["Sold"]],
            "/available",
            "Show all",
            "/",
        ),
    ]
    template = env.get_template("index.html")
    for opt in options:
        pages_total = math.ceil(len(opt.all_posts) / page_size)
        print(
            "[%d] posts found. Creating [%d] pages" % (len(opt.all_posts), pages_total)
        )

        if not os.path.exists(opt.base_folder):
            os.mkdir(opt.base_folder)

        page_folder = os.path.join(opt.base_folder, "pages")
        if not os.path.exists(page_folder):
            os.mkdir(page_folder)

        for page, posts in enumerate(take(page_size, opt.all_posts), start=1):
            if not posts:
                break

            filename = os.path.join(page_folder, f"{page}.html")
            if page == 1:
                filename = os.path.join(opt.base_folder, "index.html")

            kwargs = {
                "posts": posts,
                "page_current": page,
                "root_path": opt.root_path,
                "pages": [f"{page_folder[4:]}/{i + 1}" for i in range(pages_total)],
                "switch_message": opt.switch_message,
                "switch_path": opt.switch_path,
            }
            with open(filename, "w") as f:
                f.write(template.render(**kwargs))


if __name__ == "__main__":
    update_template(sync())
