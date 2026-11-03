# AFK OS

AFK OS is an Ubuntu 26.04 LTS and KDE Plasma distro kit by AFK Studio.
LinuxLive uses `linuxlive.yaml` and the referenced artwork to build the ISO.

    linuxlive.yaml          the spec
    assets/                 wallpaper, logos and Plymouth splash

## AFK desktop

The first login applies AFK Neon and shows a welcome notice. Open **AFK OS -
Apparence** from the applications menu at any time to switch between:

- **Bleu néon**: dark blue windows, cyan highlights, the AFK wallpaper and a
  short, centered floating dock.
- **Classique KDE**: a light, restrained blue-gray palette and a conventional
  full-width panel.
- **Noir et blanc**: high-contrast neutral colors, a monochrome AFK wallpaper
  and a centered, full-width panel inspired by Windows.

All three profiles also change the wallpaper and panel dimensions/style. The
task manager, system tray and KDE's native settings remain functional. KDE's
standard settings pages, Dolphin, SDDM and Discover are retained; the login
screen keeps the LinuxLive wallpaper. These are AFK color schemes and panel
profiles built on Breeze/Plasma, not a replacement window manager or a clone
of Windows.

## Applications and system features

- Catalog apps: Firefox, LibreOffice, VLC, Thunderbird, Steam, Heroic,
  Lutris, Discord, OBS Studio, Blender, GIMP, Krita, Kdenlive, Audacity,
  Inkscape and Visual Studio Code.
- Additional Flathub apps: Bottles, ProtonUp-Qt, Easyflatpak, Warehouse,
  jdFlatpakSnapshot, Mission Center, BleachBit, Reins
  (`dev.ibrahimcetin.reins`), Whisper, Piper and Okular.
- Ubuntu packages: Ark, KDE Connect, SMB/CIFS and network discovery tools,
  Git, Python, Docker, Wireshark, Wine, KDialog and Qt 6 D-Bus tools.

SMB1 is not enabled. Docker is installed without granting users the
root-equivalent `docker` group. AFK Store, AFK Settings and AFK AI are not
included; Discover, KDE System Settings and the AFK appearance selector
provide the available equivalents. The ISO has not been built or booted from
this Windows workspace.

## Build it in your own GitHub (no Linux needed)

1. Open https://github.com/Eric-Ness/linuxlive-distro, click "Use this
   template", then "Create a new repository". Keep it public: builds are
   free and the ISO can be downloaded.
2. In your new repository choose "Add file", then "Upload files", and drop
   in everything from this kit except this README (linuxlive.yaml and its
   folders). They replace the template's example. Commit.
3. Open the Actions tab. Build time depends on the selected applications;
   the workflow boots the ISO and checks it against the spec.
4. Open the finished run and download "iso-afk-os" under Artifacts: a zip
   with afk-os.iso and its checksum.

## Or build it on your own Linux machine

Building locally needs root, podman, QEMU and a few ISO tools; see
https://docs.linuxlive.com/spec/building-locally/ for the full list.

    git clone https://github.com/Eric-Ness/linuxlive
    cd linuxlive
    python -m pip install -r requirements.txt
    python -m linuxlive validate ../afk-os/linuxlive.yaml
    python -m linuxlive compile ../afk-os/linuxlive.yaml -o build/ctx
    sudo podman build -t localhost/afk-os build/ctx
    sudo bash scripts/assemble-iso.sh build/ctx localhost/afk-os build/afk-os.iso

## Then boot it

Put the ISO on a USB stick and start a PC from it: https://linuxlive.com/learn/
If something goes wrong: https://docs.linuxlive.com/help/failed-builds/

## Show where it came from

Paste this into your repository's README for a "Built with linuxlive" badge:

    [![Built with linuxlive](https://linuxlive.com/badge.svg)](https://linuxlive.com/)
