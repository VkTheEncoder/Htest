import requests, m3u8

def pick_hd2_sub_source(sources):
    for s in sources:
        if s.get("kind") == "sub" and (s.get("label","").upper() == "HD-2"):
            return s["url"]
    return None

def highest_quality_from_m3u8(master_url: str) -> str:
    m = m3u8.load(master_url)
    if not m.playlists:
        return master_url  # already a media playlist
    best = max(m.playlists, key=lambda p: (p.stream_info.bandwidth or 0))
    return requests.compat.urljoin(m.base_uri or master_url, best.uri)

def pick_english_sub(subtitles):
    for t in subtitles:
        if "english" in (t.get("lang","").lower()):
            return t["url"]
    return None
