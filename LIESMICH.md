# All-In Installer & Update für Batocera (Switch 2)

*Created by DeLorean23* · [English: README.md](README.md)

## Was ist das?

**All-In Installer & Update** installiert mehrere experimentelle Switch-2-Emulatoren auf einmal und packt sie alle in **ein System „Switch 2“** in Batocera. Die Spiele startest du wie gewohnt aus der Spieleliste, im Vollbild, und du legst **für jedes Spiel einzeln** fest, welcher Emulator es startet – genau wie bei Switch 1 in Batocera.

**Wofür?** Die Switch-2-Emulatoren sind noch sehr jung, und jeder von ihnen schafft andere Spiele besser. Mit diesem Installer hast du alle auf einmal, nutzt einen Spieleordner für alle und stellst bei einem Spiel, das nicht gut läuft, einfach einen anderen Emulator ein. Startest du den Installer erneut, aktualisiert er jeden Emulator, für den es einen neueren Build gibt.

## Emulatoren

| Emulator | Builds | Projekt |
|---|---|---|
| **Eglantine** (Standard) | normal + PGO | https://github.com/Djihads80/Eglantine |
| **Lichii** | normal + PGO | https://github.com/zortos293/Lichii |
| **Orchid** | normal + PGO | https://github.com/MythosOfs/Orchid |
| **Fritchii** (Linux-Build) | normal | https://github.com/xTopher1049/Fritchii-linux (Linux-Build von https://github.com/Frizti/Fritchii) |
| **Hortensia** | normal | https://github.com/justr4mzi/hortensia (fasst Lichii, Eglantine, Orchid, Selevet, SmileyTatsu, Fritchii u. a. in einem Build zusammen) |
| **Eglantine SmileyTatsu** | normal + PGO | https://github.com/SmileyTatsu/Eglantine (Mario Kart World, AMD- und NVIDIA-Anpassungen) |

Der Installer lädt immer das neueste Linux-x86_64-AppImage jedes Emulators aus dessen GitHub-Releases. Hat ein Projekt (noch) keinen Linux-Build, wird es übersprungen und als „no Linux build available“ angezeigt. Sobald es einen Build gibt, kommt der Emulator beim nächsten Lauf automatisch dazu.

**PGO**-Builds sind mit einem Profil optimiert (oft schneller). Der normale Build ist die Ausweichlösung, falls der PGO-Build auf deinem PC nicht startet oder abstürzt.

## Download

**All-In Installer & Update.zip** gibt es unter **[Releases](https://github.com/DeLorean23/All-In/releases/latest)**.

## Voraussetzungen

- Batocera v43 (x86_64-PC), Start als root (beim Start aus Ports automatisch)
- glibc 2.39 oder neuer (hat Batocera v43)
- Internetverbindung (für Download und Updates)
- Deine eigenen Spiele, Firmware und Keys

## Installation

1. Den Inhalt der ZIP nach `/userdata` entpacken, damit landen der Installer und das Cover in `/userdata/roms/ports/`.
2. In Batocera die Spieleliste aktualisieren und unter **Ports** den Eintrag **All-In Installer & Update** starten.
3. Der Installer zeigt eine Tabelle mit jedem Emulator, seinem neuesten Build und was gemacht wird.
4. Mit **y** bzw. **A** am Controller bestätigen.
5. Die Emulatoren werden nacheinander heruntergeladen und entpackt, mit Fortschrittsbalken.
   **Die erste Installation dauert etwas:** Besonders Eglantine SmileyTatsu und Hortensia sind groß, und ihr Download ist langsam. Bitte Geduld haben und das Fenster nicht schließen. Spätere Updates laden nur Emulatoren, für die es einen neueren Build gibt.
6. Am Ende fragt er „Reboot now?“. Mit **y / A** startet Batocera neu. Danach ist das System **Switch 2** in der Systemauswahl.

## Emulator für ein Spiel auswählen

- Ohne eigene Auswahl startet jedes Spiel mit **Eglantine** (normal).
- **Für ein Spiel:** in der Spieleliste die Taste auf dem Spiel gedrückt halten → Spieloptionen → **Erweiterte Spieleinstellungen → Emulator** → einen auswählen (z. B. `lichii-pgo`).
- **Für alle Spiele:** in den Systemeinstellungen von **Switch 2** einen anderen Emulator als Standard für das System wählen.

Im selben Menü kannst du unter **Switch 2 options → FULLSCREEN** ein einzelnes Spiel im Fenster starten (Standard: Vollbild).

Namen der Emulatoren im Menü: `eglantine`, `eglantine-pgo`, `lichii`, `lichii-pgo`, `orchid`, `orchid-pgo`, `fritchii`, `hortensia`, `smileytatsu`, `smileytatsu-pgo` (es stehen nur die installierten drin).

## Ordner

| Was | Wo |
|---|---|
| Spiele | `/userdata/roms/switch2/` |
| Firmware | `/userdata/bios/switch2/firmware/` |
| Keys (`prod.keys`, `title.keys`) | `/userdata/bios/switch2/keys/` |
| Spielstände, Mods, SD-Karte (für alle Emulatoren gemeinsam) | `/userdata/system/switch2/shared/` |
| Einstellungen und Shader-Cache (ein Ordner pro Emulator) | `/userdata/system/switch2/data/<emulator>/` |
| Emulatoren | `/userdata/system/switch2/emus/<emulator>/` |

Alle Emulatoren nutzen **dieselbe Firmware, dieselben Keys und dieselben Spielstände**. Jeder Emulator behält aber **seine eigenen Einstellungen**, eine Einstellung in Lichii ändert also nichts an Eglantine.

Beim ersten Anlegen setzt der Installer einmal: Vulkan, asynchrone Shader, Shader-Cache, **Region Europa, Spielsprache Deutsch**, keine Wayland-Warnung und bei Hortensia die Menüsprache English (ohne Sprachabfrage). Danach werden die Einstellungen nie wieder überschrieben.

**Hinweis zu den Key-Dateien:** Die Keys sind nur für **Switch-1**-Dateien (`.nsp`, `.xci`, …) wichtig. Switch-2-Spielordner (`name.s2`) brauchen sie nicht.

### Spielformate

- **Switch 2:** ein Spielordner mit der Endung `.s2` (z. B. `Mario Kart World.s2/`), in dem `exefs/main` liegt
- **Dateien:** `.nsp` `.nsz` `.nup` `.xci` `.xcz` `.nca` `.nro` `.nso` `.kip`

## Einstellungen eines Emulators

**F1-Dateimanager → Anwendungen → Switch 2 Eglantine** (und `Switch 2 Eglantine PGO`, `Switch 2 Lichii`, …). Jeder installierte Emulator hat einen eigenen Eintrag und öffnet sich ohne Spiel.

## Controller

- **Controller ab dem ersten Start, ohne Umstellen:** Schon bei der Installation wird der angeschlossene Controller in alle Emulatoren eingetragen (Controller 1 = Spieler 1, … bis 8), mit derselben Standardbelegung, die der Emulator selbst nimmt, wenn man von Tastatur auf Controller umstellt. Die anderen Emulatoren übernehmen dabei die Einstellung von Eglantine.
  - Das passiert nur, solange ein Emulator noch auf Tastatur steht (auch vor einem Spielstart, falls beim Installieren kein Controller an war). Danach wird die Belegung nie mehr angefasst, eigene Änderungen über F1 bleiben.
- **Hotkey + Start** (Select + Start oder Guide + Start) beendet das Spiel.
- Pop-up-Fenster vor dem Spielstart (z. B. „Empfohlene Einstellungen verwenden?“) gehen mit dem Controller: Steuerkreuz zum Auswählen, **A** = bestätigen, **B** = abbrechen. Dafür starten die Emulatoren im X11-Modus (wenn Batocera ihn anbietet).

## Update

Den Installer **All-In Installer & Update** einfach erneut unter **Ports** starten. Jeder Emulator wird einzeln geprüft:

- **new**: noch nicht installiert → wird installiert
- **update**: neuerer Build da → wird installiert, die vorherige Version bleibt in `/userdata/system/switch2/backup/`
- **up to date**: nichts zu tun

Ist alles aktuell, steht „up to date“. Nach einem Update ist kein Neustart nötig.

## Umstieg vom „Eglantine Installer & Updater“

Beim ersten Lauf übernimmt der Installer deine Spielstände, Mods und Eglantine-Einstellungen aus `/userdata/system/eglantine` und ersetzt das alte System „Switch 2“. Danach:

- den alten **Eglantine Installer & Updater** aus Ports löschen (ein erneuter Start würde das Switch-2-System dieses Installers ersetzen),
- den Ordner `/userdata/system/eglantine` kannst du löschen, um Platz zu sparen.

## Hinweise

- Alle diese Emulatoren sind sehr experimentell. Nicht jedes Spiel läuft, und ein Spiel kann in einem Emulator laufen und im anderen nicht.
- Das ist ein inoffizielles System. Ein späteres Batocera-Update kann es beeinflussen.
- Dieses Projekt stellt keine Spiele, Firmware oder Keys bereit.
- Log-Dateien bei Problemen: `/userdata/system/logs/allin-installer.log` und `/userdata/system/logs/switch2.log`

## Bauen

`./build.sh` erstellt die ZIP in `dist/` aus `src/installer.template.sh`, den Hilfsskripten in `src/` und `assets/cover.jpg`.

## Lizenz

Der Installer steht unter der [MIT-Lizenz](LICENSE). Jeder Emulator ist ein eigenes Projekt mit eigener Lizenz; dieser Installer lädt sie nur aus ihren offiziellen Releases herunter.
