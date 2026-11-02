# Make your own Linux distro

This template builds a live Linux distro from one short file,
[`linuxlive.yaml`](linuxlive.yaml). Pick Ubuntu or Fedora, a desktop, some
apps and your own wallpaper and logo. GitHub Actions then builds an ISO that
boots from a USB stick or in a virtual machine, on BIOS and UEFI PCs with
Secure Boot on. Each build is booted five ways and checked before you
download it.

You need a GitHub account and nothing else: no Linux, no installs.

## 1. Make your copy

Click **Use this template** → **Create a new repository**, give it a name,
and create it.

Keep it **public**. Builds are free in public repositories and the ISO can be
downloaded. A private repository works too, but builds use your account's
Actions minutes, and GitHub Free's artifact storage (500 MB) is too small to
hold an ISO.

GitHub may start a build of the unchanged example straight away. Let it run,
or cancel it from the **Actions** tab.

## 2. Describe your distro

Open `linuxlive.yaml` and click the pencil to edit it in your browser:

```yaml
schema_version: 1
name: My Distro
version: "0.1"
base: ubuntu
desktop: cinnamon
apps:
  - firefox
  - vlc
branding:
  wallpaper: assets/wallpaper.png
  logo: assets/logo.png
  accent_color: "#c2185b"
```

- `base`: `ubuntu` (Ubuntu 26.04 LTS) or `fedora` (Fedora 44).
- `desktop`: `gnome`, `kde` or `cinnamon`.
- `apps`: any of the 20 apps in the
  [catalog](https://docs.linuxlive.com/spec/catalog/#apps),
  such as `libreoffice`, `gimp`, `steam` or `gcompris`.
- Keep the quotes around `version` and `accent_color`.

The [spec reference](https://docs.linuxlive.com/spec/reference/) explains every option, and
[the docs](https://docs.linuxlive.com/) cover the rest.

## 3. Add your art

Replace the two images in [`assets/`](assets), keeping their names. In the
`assets` folder, choose **Add file** → **Upload files**.

- `wallpaper.png`: a PNG of at least 1280×720 with **one strong colour**,
  such as grass, sky or a bold gradient. The build checks that your
  wallpaper's colour really shows on the desktop, so a mostly grey, black or
  white picture fails that check. Save it as an ordinary 8-bit PNG, not
  16-bit or interlaced.
- `logo.png`: a square PNG of exactly 128, 256 or 512 pixels. It appears on
  the boot screen, in About screens and, on Cinnamon, as the menu button.

## 4. Build it

Commit your changes to `main`. That starts a build. Watch it in the
**Actions** tab, where it takes about 20 minutes for Ubuntu and 40 for Fedora.
To build again without changing anything, choose **Actions** → **build** →
**Run workflow**.

A live ISO never updates itself, so the workflow also rebuilds your distro
once a month (on the 7th) with the newest packages and security fixes.
GitHub pauses that after 60 days without a commit to the repository; to turn
it back on, click **Enable workflow** in the **Actions** tab, or **Rebuild
now** on linuxlive.com's My distros page. To stop it, delete the `schedule:` lines in
[`.github/workflows/build.yml`](.github/workflows/build.yml).

## 5. Download and boot it

Open the finished run and scroll to **Artifacts**. Download
**iso-my-distro**, which is named after your distro. It's a zip with the ISO
and its SHA-256 checksum, and it's kept for 7 days. The run's summary shows
every check that passed.

Then try it in VirtualBox, or write it to a USB stick of 8 GB or more with
Rufus (DD mode), Fedora Media Writer or balenaEtcher.
The docs cover [VirtualBox](https://docs.linuxlive.com/help/virtualbox/) and
[USB sticks](https://docs.linuxlive.com/help/usb-stick/): checksums, settings, writers and boot keys.

## If the build fails

Open the failed step to see why.

- **Check the spec**: the message names the problem, for example a missing
  quote or an unknown app.
- **Verify**: one of the checks on the booted system failed. If it's about
  the wallpaper's colour, use a more colourful PNG.

[Why a build fails](https://docs.linuxlive.com/help/failed-builds/) goes through the common causes.
Anything else: [open an issue](https://github.com/Eric-Ness/linuxlive/issues)
with a link to your run.

## Good to know

- The ISO runs live (nothing is saved when you shut down) and can install
  itself: the "Install" desktop icon or boot-menu entry erases one whole disk
  and installs your distro. Fedora-based distros install from the system
  image each build publishes to this repository's packages, so installing
  them needs the internet, and installed systems update from it. See
  [Known limits](https://docs.linuxlive.com/help/known-limits/).
- Your spec can also add packages, files, your own scripts (run while the
  image is built, at an installed computer's first start, or at each user's
  first login) and code from GitHub. Put scripts in `scripts/` and files in
  `files/`; see
  [Extras](https://docs.linuxlive.com/workshop/extras/) and the
  [spec reference](https://docs.linuxlive.com/spec/reference/#packages).
- Builds use [linuxlive](https://github.com/Eric-Ness/linuxlive) v0.9.2. To
  move to a newer release, change `@v0.9.2` in
  [`.github/workflows/build.yml`](.github/workflows/build.yml).
- This template is under the MIT No Attribution licence, so your distro's
  files are yours to license however you like. linuxlive itself is GPL-3.0.
