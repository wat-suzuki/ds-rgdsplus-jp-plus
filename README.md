[English](README.md) | [日本語](README.ja.md)

# monoDS RG DS PLUS

A Japanese-language package based on [DEDICATED OS for the RG DS Plus](https://github.com/dedicated-os/dedicated-rgds-plus), retaining the original author's attribution and licensing.

This release can boot with either a TF1 card alone or both TF1 and TF2 cards. It also adds Japanese ROM support and Hi-Res 3D support.

| <img width="320" src="github/bootlogo-1.png" alt="Bootlogo" /> | <img width="320" src="github/original.png" alt="Original display" /> |
| :---: | :---: |
| **Bootlogo** | **Original** |
| <img width="320" src="github/2x.png" alt="x2 display" /> | <img width="320" src="github/hi-res3d.png" alt="Hi-RES display" /> |
| **x2** | **Hi-RES** |

### x2

x2 (Scale2x) is a display mode intended to improve image quality while preserving the original pixel look and smoothing edges. Its appearance depends on the game and personal preference, so compare it with Original and choose the one you prefer. Example: **Pokémon Ranger**.

### Hi-RES

Hi-RES increases the resolution of 3D rendering. It can improve image quality in 3D-focused games such as **Pokémon Ranger** and **Mario Kart DS**. In 2D-focused games such as **New Super Mario Bros.**, it can look worse than the original rendering. Switch modes per game and choose the display you prefer.

## Differences from DEDICATED OS

- Japanese ROM game titles are supported.
- Hi-Res 3D is supported.
- The system can boot with a TF1 card alone.

## Installation

### Using TF1 only

1. Download and extract the latest monoDS RG DS PLUS package from [Releases](../../releases).
2. Copy the package contents to the root of the TF1/INT card.
3. Put your games in `/games/`, insert the card into the TF1/INT slot, and start the device.

### Using TF1 and TF2

1. Download the system image from the original [`main-rgds-plus` releases](https://github.com/dedicated-os/main-rgds-plus/releases) and write it to the TF1/INT card, following the [original project instructions](https://github.com/dedicated-os/dedicated-rgds-plus).
2. Prepare the TF2/EXT card as described by the original project.
3. Download and extract the latest monoDS RG DS PLUS package from this repository's [Releases](../../releases), then copy its contents to the root of TF2/EXT.
4. Put your games in `/games/` on TF2/EXT, insert both cards, and start the device.

### Updating

1. Download and extract the latest monoDS RG DS PLUS package from [Releases](../../releases).
2. Copy `system.zip`, `bootlogo-0.bmp`, and `bootlogo-1.bmp` to the root of the card in use, replacing the existing files (TF1/INT for a TF1-only setup, or TF2/EXT for a two-card setup).
3. Start the device. The system update is applied during startup.

## Controls

Press the device's **MENU** button to open the in-game menu. Press it again to open the system menu.

| Action | Shortcut |
| :--- | :--- |
| Toggle Hi-Res mode | `MENU + START` |
| Swap the top and bottom screens | `MENU + SELECT` |
| Toggle the screen grid | `MENU + R2` |
| Save a screenshot | `MENU + A` |
| Adjust brightness | `MENU + Volume + / Volume -` |
| Fast-forward | `BACK` |

![Boot controls](github/bootlogo-1-preview.png)

`MENU + A` saves both screens together as one 1024×1536 BMP in `userdata/screenshots/`, named with the game title and an increasing serial (for example, `Game Title-0001.bmp`).

Changing Hi-Res mode saves the current game, restarts DraStic, and resumes the game automatically.

## Credits

DEDICATED OS for the RG DS Plus, which this project builds on, is created and maintained by [shauninman](https://github.com/dedicated-os/dedicated-rgds-plus). Please see the [original project](https://github.com/dedicated-os/dedicated-rgds-plus) for its documentation and licensing.
