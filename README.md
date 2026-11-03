# AFK OS

AFK OS is a LinuxLive-based Ubuntu 26.04 / KDE Plasma live system by AFK Studio.
The kit configures its wallpaper, blue accent, Plymouth boot splash, dock,
applications and selected system packages.

LinuxLive's distro specification does not currently expose a custom KDE theme,
SDDM login theme, or separate developer/author metadata. The desktop and login
screen therefore retain their supported KDE defaults; this kit does not claim
to provide a complete redesign of every Plasma or login interface.

The applications are installed from the LinuxLive catalog or Flathub. The
additional Ubuntu packages provide archive management, Windows network shares,
development tools, Wireshark and Wine/Winetricks. Wine and game compatibility
depend on the application, hardware, drivers and required 32-bit support; they
are not universal.

## Applications included

LinuxLive catalog: Firefox, LibreOffice, VLC, Thunderbird, Steam, Discord,
Visual Studio Code, Audacity, GIMP, Inkscape, Krita, Blender, OBS Studio,
Kdenlive, Lutris and Heroic Games Launcher.

Additional Flathub apps: Okular, Bottles, ProtonUp-Qt, Easyflatpak, Warehouse,
jdFlatpakSnapshot, Mission Center, BleachBit, Reins, Whisper, Piper and Akizip.

Ubuntu packages: KDE Connect, Ark, Samba, SMB/CIFS and Avahi tools, Git,
Python 3, Docker, Wireshark, Wine, Winetricks, curl and zstd.

## Maxence, assistant local

Maxence appears in the KDE application menu. Its French-language interface runs
in its own Firefox window, and a Maxence shortcut is installed on the desktop.
Click that shortcut to open the window, and click it again to close just
Maxence; the rest of the user's Firefox windows are left alone. Its interface
sends questions only to the local Ollama service (`127.0.0.1`), using
`qwen2.5:1.5b`. Chat history stays in Maxence's dedicated Firefox profile;
Maxence cannot inspect files or operate the computer.

The Ollama runtime is installed while the image is built. On the first launch,
Maxence downloads the model from Ollama, so an Internet connection is required
once; the model is kept on the computer for later offline use. The ISO and
installed system therefore need enough free disk space for the runtime and
model. Answers can be inaccurate and should be checked when it matters.

AFK Store and AFK Settings are not included: the supplied kit contains no source
or installable packages for those projects. No AFK Update component has been
added.

    linuxlive.yaml          the spec
    assets/                 wallpaper and logo

## Build it in your own GitHub

1. Open https://github.com/Eric-Ness/linuxlive-distro, click "Use this
   template", then "Create a new repository". Keep it public: builds are
   free and the ISO can be downloaded.
2. In your new repository choose "Add file", then "Upload files", and drop
   in everything from this kit except this README (linuxlive.yaml and its
   folders). They replace the template's example. Commit.
3. Open the Actions tab. The build takes about 20 minutes for Ubuntu and 40
   for Fedora; it boots the ISO five ways and checks it against your spec.
4. Open the finished run and download "iso-afk-os" under Artifacts: a zip
   with afk-os.iso and its checksum.

## Or build it on your own Linux machine

Building the ISO locally needs Linux (or WSL2), root, podman, QEMU and a few ISO
tools; see https://docs.linuxlive.com/spec/building-locally/ for the full list.

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
