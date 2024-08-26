# Music Player

A MILI UI demo featuring a rich music player.<br>
[MILI Github](https://github.com/damusss/mili), [MILI PyPI](https://pypi.org/project/mili-ui/)

## Supported Formats

**Audio and Video**: MP4

**Audio Only**: WAV, MP3, OGG, FLAC, OPUS, WV, MOD, AIFF

**Unsupported Track Positioning**: WAV, OPUS, WV, AIFF

## Features

30/60 FPS
Async loading
Power saving

### Playlists

- Rename
- Delete
- Empty/Load from folder
- Reorder
- Reset/Upload/Auto-generate cover

### Musics

- Rename
- Add/Delete
- Reorder
- Change playlist
- Score-based Search

### Player

- Volume/Mute
- Play/Pause
- Next/Previous/Auto-next
- Music loop
- Playlist loop
- Playlist shuffle
- MP4 Video Player
- BG Effects
- History

### Miniplayer

# Building/Running

Make sure to be in the folder where the main file is located, then:

```
pip install -r requirements.txt
py MusicPlayer.py
```

You can use the health_check.py script to check for unused files in the data folder. Use the --remove argument to delete them automatically. The script is also run when the music player starts.

# Dependencies

- `pygame-ce` >= 2.5.1 (music, windowing, input, rendering backend)
- `mili-ui` >= 0.9.2 (UI backend)
- `moviepy` >= 1.0.3 (MP4 converter/reader)
- **[optional]** `PySDL2` >= 0.9.16 (global mouse state backend)

# Codebase Notice

The codebase currently follows the following conventions (they are not hard rules):

- `__init__` and `init(_*)` methods are called once.
- Every method starting with `ui_` is only responsible for organizing and rendering the UI components. The main `ui` function of each UI component is split in several subfunctions for ease of readibility.
- Every method starting with `action_` is almost certainly a callback that is _only_ called following a user UI interaction, and never called from anywhere else.
- Methods starting with `get_`, despite the name, are usually called within the same class to change internal states without returning anything.
- Every normal method is used internally by the class and usually by external classes to manage the states.
