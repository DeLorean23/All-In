# All-In Installer & Update for Batocera (Switch 2)

*Created by DeLorean23* · [Deutsche Anleitung: LIESMICH.md](LIESMICH.md)

## What is this?

**All-In Installer & Update** installs several experimental Switch 2 emulators in one go and puts them all into **one system "Switch 2"** in Batocera. You start your games from the normal game list, in fullscreen, and you decide **per game** which emulator runs it — the same way as with Switch 1 in Batocera.

**Why?** The Switch 2 emulators are very young and every one of them runs different games better. With this installer you have all of them at once, use one games folder for all of them, and simply switch the emulator for a game that does not run well. Run the installer again and it updates every emulator that has a newer build.

## Emulators

| Emulator | Builds | Project |
|---|---|---|
| **Eglantine** (default) | normal + PGO | https://github.com/Djihads80/Eglantine |
| **Lichii** | normal + PGO | https://github.com/zortos293/Lichii |
| **Orchid** | normal + PGO | https://github.com/MythosOfs/Orchid |
| **Fritchii** (Linux build) | normal | https://github.com/xTopher1049/Fritchii-linux (Linux build of https://github.com/Frizti/Fritchii) |

The installer always downloads the newest Linux x86_64 AppImage of each emulator from its GitHub releases. If a project has no Linux build (yet), it is skipped and shown as "no Linux build available"; it is added automatically on a later run as soon as a build exists.

**PGO** builds are optimised with a profile (often faster). The normal build is the fallback if the PGO build does not start or crashes on your PC.

## Download

Get **All-In Installer & Update.zip** from the **[Releases](https://github.com/DeLorean23/All-In/releases/latest)** page.

## Requirements

- Batocera v43 (x86_64 PC), run as root (the default when started from Ports)
- glibc 2.39 or newer (Batocera v43 has it)
- Internet connection (for download and updates)
- Your own games, firmware and keys

## Installation

1. Extract the contents of the ZIP archive to `/userdata`. This places the installer and its cover image in `/userdata/roms/ports/`.
2. In Batocera, refresh the game list and launch **All-In Installer & Update** from **Ports**.
3. The installer shows a table with every emulator, its newest build and what will be done.
4. Confirm with **y** or **A** on your controller.
5. Every emulator is downloaded and unpacked, one after the other, with a progress bar.
6. At the end it asks "Reboot now?". Press **y / A** to restart Batocera. After the reboot the system **Switch 2** is in the system list.

## Choosing the emulator for a game

- Without your own choice every game starts with **Eglantine** (normal).
- **For one game:** hold the button on the game in the game list → game options → **advanced game options → emulator** → pick one (for example `lichii-pgo`).
- **For all games:** in the system settings of **Switch 2** choose another emulator as the default for the system.

In the same menu, **Switch 2 options → FULLSCREEN** lets you start a single game in a window (default: fullscreen).

Emulator names in the menu: `eglantine`, `eglantine-pgo`, `lichii`, `lichii-pgo`, `orchid`, `orchid-pgo`, `fritchii` (only the installed ones are listed).

## Folders

| What | Where |
|---|---|
| Games | `/userdata/roms/switch2/` |
| Firmware | `/userdata/bios/switch2/firmware/` |
| Keys (`prod.keys`, `title.keys`) | `/userdata/bios/switch2/keys/` |
| Saves, mods, SD card (shared by all emulators) | `/userdata/system/switch2/shared/` |
| Settings and shader cache (one folder per emulator) | `/userdata/system/switch2/data/<emulator>/` |
| Emulators | `/userdata/system/switch2/emus/<emulator>/` |

All emulators use the **same firmware, keys and saves**. Every emulator keeps **its own settings**, so a setting in Lichii does not change Eglantine.

**Note on the key files:** the keys are only important for **Switch 1** files (`.nsp`, `.xci`, ...). Switch 2 game folders (`name.s2`) do not need them.

### Game formats

- **Switch 2:** a game folder with the ending `.s2` (for example `Mario Kart World.s2/`) that contains `exefs/main`
- **Files:** `.nsp` `.nsz` `.nup` `.xci` `.xcz` `.nca` `.nro` `.nso` `.kip`

## Settings of an emulator

**F1 file manager → Applications → Switch 2 Eglantine** (and `Switch 2 Eglantine PGO`, `Switch 2 Lichii`, ...). Every installed emulator has its own entry and opens without a game.

## Controller

- **Controllers work right away, no keyboard setup:** before every start (game or F1 entry) the connected controllers are written into the settings of the chosen emulator: controller 1 = player 1, controller 2 = player 2, ... up to 8. Buttons by position like on the Switch (Xbox/PlayStation pads too), sticks, triggers, motion and rumble included. This happens on every start, so it always fits, even after changing the controller. Manual changes of the controller settings inside an emulator are replaced on the next start.
- **Hotkey + Start** (Select + Start or Guide + Start) closes the game.
- Pop-up windows before a game starts (for example "Use the recommended settings?") can be answered with the controller: D-pad to choose, **A** = confirm, **B** = cancel.

## Update

Simply launch **All-In Installer & Update** again from **Ports**. Every emulator is checked on its own:

- **new**: not installed yet → will be installed
- **update**: newer build available → will be installed, the previous version is kept in `/userdata/system/switch2/backup/`
- **up to date**: nothing to do

If everything is current, the installer shows "up to date". No reboot is required after an update.

## Coming from the "Eglantine Installer & Updater"

On the first run the installer takes over your saves, mods and Eglantine settings from `/userdata/system/eglantine` and replaces the old "Switch 2" system. Afterwards:

- delete the old **Eglantine Installer & Updater** from Ports (running it again would replace the Switch 2 system of this installer),
- you can delete the folder `/userdata/system/eglantine` to free space.

## Notes

- All of these emulators are very experimental. Not every game runs, and a game may run in one emulator but not in another.
- This is an unofficial system. A future Batocera update may affect it.
- This project does not provide any games, firmware or keys.
- Log files for troubleshooting: `/userdata/system/logs/allin-installer.log` and `/userdata/system/logs/switch2.log`

## Building

`./build.sh` creates the ZIP in `dist/` from `src/installer.template.sh`, the helper scripts in `src/` and `assets/cover.jpg`.

## License

The installer is released under the [MIT License](LICENSE). Each emulator is a separate project with its own license; this installer only downloads them from their official releases.
