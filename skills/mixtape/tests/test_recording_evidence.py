import copy
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import canonicalize
import youtube_playlist as yt


class RecordingEvidenceTests(unittest.TestCase):
    def setUp(self):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        self.directory = Path(root.name)
        self.path = self.directory / "raw.json"
        self.sealed = self.directory / "pinned.json"
        self.tracks = [
            {"title": "One", "artists": ["Artist"], "youtubeVideoId": "clip0000001",
             "durationSeconds": 1800, "version": "Official audio"},
            {"title": "Two", "artists": ["Artist"], "youtubeVideoId": "clip0000002",
             "youtubeDurationSeconds": 1800},
        ]
        self.save({"tracklist": self.tracks})

    def save(self, data):
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def run_cli(self, *args):
        with redirect_stdout(StringIO()) as output:
            status = yt.main([str(self.path), *map(str, args)])
        return status, json.loads(output.getvalue())

    def test_catalog_rewrite_preserves_ids_durations_and_independent_fingerprints(self):
        def match(title, *args, **kwargs):
            return {"title": title + " (Catalog)", "artists": "Artist"}, {"status": "confirmed"}

        argv = ["canonicalize.py", str(self.path), "--out", str(self.sealed)]
        with patch.object(sys, "argv", argv), patch.object(canonicalize, "canonicalize_track", side_effect=match), redirect_stdout(StringIO()):
            self.assertEqual(canonicalize.main(), 0)
        saved = json.loads(self.sealed.read_text())
        self.assertEqual(saved["tracklist"][0]["version"], "Official audio")
        self.assertEqual(saved["tracklist"][0]["title"], "One (Catalog)")
        self.assertEqual(yt.expected_ids(saved), ["clip0000001", "clip0000002"])
        self.assertEqual(saved["_mixtape"]["youtubeTotalDurationSeconds"], 3600)
        self.assertEqual(saved["_mixtape"]["youtubeRecordingSha256"],
                         canonicalize.youtube_recording_evidence(self.tracks)["youtubeRecordingSha256"])
        for edit in (
            lambda tracks: tracks[0].update(youtubeVideoId="clip0000003"),
            lambda tracks: tracks[0].update(durationSeconds=1799),
            lambda tracks: tracks.reverse(),
        ):
            tampered = copy.deepcopy(saved)
            edit(tampered["tracklist"])
            with self.assertRaises(ValueError):
                yt.expected_ids(tampered)
            self.save(tampered)
            with patch.object(sys, "argv", argv), patch.object(canonicalize, "canonicalize_track") as search, redirect_stderr(StringIO()):
                self.assertEqual(canonicalize.main(), 2)
                search.assert_not_called()

    def test_exact_source_path_and_range_boundaries(self):
        for total, accepted in [(3479,False),(3480,True),(3720,True),(3721,False)]:
            with self.subTest(total=total):
                self.tracks[0]["durationSeconds"] = total - 1800
                self.save({"tracklist":self.tracks})
                outfile = self.directory / f"{total}.json"
                code, result = self.run_cli("--pin-recordings", outfile, "--duration-range", 58, 62)
                self.assertEqual(code, 0 if accepted else 2)
                self.assertEqual(outfile.exists(), accepted)
                if accepted:
                    self.assertEqual(result["youtubeTotalDurationSeconds"], total)
                    self.assertNotIn("catalogVerified", json.loads(outfile.read_text())["_mixtape"])
        self.tracks[1] = copy.deepcopy(self.tracks[0])
        self.save({"tracklist":self.tracks})
        self.assertEqual(self.run_cli("--pin-recordings", self.sealed)[0], 0)
        pinned = json.loads(self.sealed.read_text())
        self.assertEqual(yt.expected_ids(pinned), ["clip0000001"] * 2)
        self.save(pinned)
        with patch.object(yt, "read_playlist", return_value=["clip0000001"] * 2):
            code, result = self.run_cli("--playlist-id", "PLsaved")
            self.assertEqual((code,result["status"]), (0,"verified"))
            self.assertEqual(result["youtubeTotalDurationSeconds"], self.tracks[0]["durationSeconds"] * 2)

    def test_missing_conflicting_and_invalid_durations(self):
        for value in [None, True, 0, -5, 1800.1, "1800"]:
            self.tracks[0]["durationSeconds"] = value
            self.save({"tracklist":self.tracks})
            self.assertEqual(self.run_cli("--pin-recordings", self.sealed)[0], 2)
        self.tracks[0]["durationSeconds"] = 1800
        self.tracks[0]["youtubeDurationSeconds"] = 1799
        self.save({"tracklist":self.tracks})
        self.assertEqual(self.run_cli("--pin-recordings", self.sealed)[0], 2)
        del self.tracks[0]["durationSeconds"], self.tracks[0]["youtubeDurationSeconds"]
        self.save({"tracklist":self.tracks})
        self.assertEqual(self.run_cli("--pin-recordings", self.sealed, "--duration-range", 58, 62)[0], 2)
        self.assertEqual(self.run_cli("--pin-recordings", self.sealed)[1]["youtubeTotalDurationSeconds"], None)

    def test_legacy_catalog_only_does_not_authorize_changed_exact_recordings(self):
        self.save({"tracklist":self.tracks, "_mixtape":{
            "catalogVerified":True, "tracklistSha256":canonicalize.tracklist_fingerprint(self.tracks)}})
        with patch.object(yt, "read_playlist") as read:
            self.assertEqual(self.run_cli("--playlist-id", "PLsaved")[0], 2)
            read.assert_not_called()
        prepared = self.run_cli("--write-urls", self.directory / "list.txt")[1]
        self.assertEqual(prepared["status"], "prepared")
        self.assertFalse(prepared["recordingFingerprintPresent"])
