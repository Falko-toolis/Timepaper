# Timepaper

A time-based wallpaper changer for Windows. Drop your images in the `wallpapers/` folder, name them by time (e.g. `18,00.jpg`), and Timepaper switches your desktop background automatically throughout the day. No CPU waste, no config files.

---

<details>
<summary>Requirements & Installation</summary>

Requires Python 3.10 or later.

Double-click `install.bat`, or run manually in a terminal:

```bash
pip install -r requirements.txt
```

</details>

<details>
<summary>How it works</summary>

Timepaper reads your `wallpapers/` folder at startup and builds a schedule from the filenames. It applies the correct wallpaper immediately, then sleeps precisely until the next scheduled change. No polling, no background loops eating your CPU.

PNG files are automatically converted to high-quality JPEG before being applied, avoiding the color degradation Windows introduces when handling PNGs natively.

</details>

<details>
<summary>Naming your images</summary>

Rename each image to `HH,MM.ext` — use a comma instead of a colon since Windows doesn't allow colons in filenames.

| Filename | Triggers at |
|---|---|
| `08,00.jpg` | 08:00 |
| `11,00.png` | 11:00 |
| `18,00.jpg` | 18:00 |
| `21,00.png` | 21:00 |

Supported formats: `.jpg`, `.jpeg`, `.png`, `.bmp`. No limit on the number of images.

</details>

<details>
<summary>Usage</summary>

Double-click `app.pyw`. No console window will appear. Timepaper runs silently in the system tray with two options:

- **Apply now** — forces the current wallpaper to apply immediately
- **Quit** — stops Timepaper

</details>

<details>
<summary>Launch at startup</summary>

Press `Win + R`, type `shell:startup`, and drop a shortcut to `app.pyw` into that folder.

</details>

<details>
<summary>Folder structure</summary>

```
Timepaper/
├── app.pyw
├── install.bat
├── requirements.txt
├── README.md
├── how to use.htm
└── wallpapers/
    ├── 08,00.jpg
    ├── 11,00.png
    ├── 18,00.jpg
    └── 21,00.png
```

The `.cache/` folder is created automatically to store converted JPEG copies of your images. You can safely delete it at any time.

</details>
