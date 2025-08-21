from typing import List, Dict

class Provider:
    def list_episodes(self, anilist_id: int) -> List[Dict]:
        """
        Return: [{ "ep_id": "s1e1", "number": 1, "title": "Episode 1" }, ...]
        """
        raise NotImplementedError

    def get_episode_sources(self, ep_id: str) -> Dict:
        """
        Return:
        {
          "sources": [
            {"label": "HD-1", "kind": "sub", "url": "https://.../master.m3u8"},
            {"label": "HD-2", "kind": "sub", "url": "https://.../master.m3u8"},
            {"label": "HD-1", "kind": "dub", "url": "https://..."}
          ],
          "subtitles": [
            {"lang": "English", "url": "https://.../en.vtt"},
            {"lang": "German - CR", "url": "https://.../de.vtt"}
          ]
        }
        """
        raise NotImplementedError

class MyLegalProvider(Provider):
    """
    EXAMPLE ONLY.
    Replace with your own/authorized links (S3/R2/CDN/official API).
    """
    def list_episodes(self, anilist_id: int) -> List[Dict]:
        return [
            {"ep_id": f"{anilist_id}-s1e1", "number": 1, "title": "Episode 1"},
            {"ep_id": f"{anilist_id}-s1e2", "number": 2, "title": "Episode 2"},
        ]

    def get_episode_sources(self, ep_id: str) -> Dict:
        return {
            "sources": [
                {"label": "HD-1", "kind": "sub", "url": "https://example.com/demo/hd1/master.m3u8"},
                {"label": "HD-2", "kind": "sub", "url": "https://example.com/demo/hd2/master.m3u8"},
                {"label": "HD-1", "kind": "dub", "url": "https://example.com/demo/dub/master.m3u8"},
            ],
            "subtitles": [
                {"lang": "English", "url": "https://example.com/subs/en.vtt"},
                {"lang": "German - CR", "url": "https://example.com/subs/de.vtt"},
            ]
        }
