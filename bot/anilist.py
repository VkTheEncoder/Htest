import requests

ANILIST_URL = "https://graphql.anilist.co"
ANILIST_SEARCH_Q = """
query ($q: String) {
  Page(perPage: 8) {
    media(search: $q, type: ANIME) {
      id
      title { romaji english native }
      episodes
    }
  }
}
"""

def search_anime(query: str):
    resp = requests.post(ANILIST_URL, json={"query": ANILIST_SEARCH_Q, "variables": {"q": query}})
    resp.raise_for_status()
    arr = resp.json()["data"]["Page"]["media"]
    out = []
    for m in arr:
        title = m["title"]["english"] or m["title"]["romaji"] or m["title"]["native"]
        out.append({"id": m["id"], "title": title, "episodes": m.get("episodes")})
    return out
