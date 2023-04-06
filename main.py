import os
from datetime import datetime

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader("html"),
    autoescape=select_autoescape()
)


def sync():
    aids = os.getenv("ARTIST_IDS")
    if not aids:
        print("No artist ids found. Exiting")
        return

    aids = aids.split(",")
    print("[%d] artist ids found" % len(aids))

    url = "https://www.dailypaintworks.com/Home/SearchPostsResults"
    payload = {
        "inSearchId": "1680581114640",
        "inSitePage": "GALLERY",
        "inByDate": "false",
        "inCurrentDate": datetime.now().strftime("%M/%D/%Y"),
        "inPageNumber": "0",
        "inDisplayedPostCount": "0",
        "isInArrangeMode": "false"
    }
    headers = {
      'Accept': '*/*',
      'Accept-Language': 'en-US,en;q=0.5',
      'Accept-Encoding': 'gzip, deflate, br',
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'Pragma': 'no-cache',
      'Cache-Control': 'no-cache',
    }

    data = []
    for aid in aids:
        payload["inArtistId"] = aid
        res = requests.request("POST", url, headers=headers, data=payload)
        assert res.status_code == 200, res.text
        data.append(res.json())

    data = sorted(
        sum([d["Posts"] for d in data], []),
        key=lambda p: (
            datetime.strptime(p["DateString"], "%b %d, %Y"),
            p["GalleryName"]
        ),
        reverse=True
    )
    return data


def update_template(posts):
    if not posts:
        return

    template = env.get_template("index.html")
    with open(os.path.join("docs", "index.html"), "w") as f:
        f.write(template.render(posts=posts))


if __name__ == "__main__":
    update_template(sync())
