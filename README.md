[English](README.md) | [日本語](README.ja.md)

# DS RGDSPLUS JP+

An unofficial Japanese-language adaptation of [DEDICATED OS for RG DS Plus](https://github.com/dedicated-os/dedicated-rgds-plus). This project is based on and intended to complement the original work by its author.

It adds Japanese game title display and a shortcut to switch Hi-Res mode on or off.

## Installation

The RG DS Plus uses two SD cards. Use the original system image on TF1/INT, and install the launcher package on TF2/EXT.

### Fresh installation

1. Download the original `main-rgds-plus` system image from the [official releases](https://github.com/dedicated-os/main-rgds-plus/releases) and write it to the TF1/INT card, following the [original project instructions](https://github.com/dedicated-os/dedicated-rgds-plus).
2. Prepare the TF2/EXT card as described by the original project.
3. Download the latest JP+ package from this repository's [Releases](../../releases), extract it, and copy its contents to the root of TF2/EXT.
4. Put your games in `/games/` on TF2/EXT, then insert both cards and start the device.

### Updating JP+

1. Download and extract the latest JP+ package from [Releases](../../releases).
2. Copy `system.zip`, `bootlogo-0.bmp`, and `bootlogo-1.bmp` to the root of TF2/EXT, replacing the existing files.
3. Start the device. The system update is applied during startup.

## Controls

Press the device's **MENU** button to open the in-game menu. Press it again to open the system menu.

| Action | Shortcut |
| :--- | :--- |
| Toggle Hi-Res mode | `MENU + START` |
| Swap the top and bottom screens | `MENU + SELECT` |
| Toggle the screen grid | `MENU + L2` |
| Save a screenshot | `MENU + A` |
| Adjust brightness | `MENU + Volume + / Volume -` |
| Fast-forward | `BACK` |

![Boot controls](github/bootlogo-1-preview.png)

Changing Hi-Res mode saves the current game, restarts DraStic, and resumes the game automatically.

## Credits

DEDICATED OS for RG DS Plus is created and maintained by [shauninman](https://github.com/dedicated-os/dedicated-rgds-plus). Please see the [original project](https://github.com/dedicated-os/dedicated-rgds-plus) for its documentation and licensing.
