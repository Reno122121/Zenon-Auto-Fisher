# Publish Zenon with GitHub Desktop

## Repository details

- **Name:** `zenon-fishing-helper`
- **Description:** `A Windows Python helper for a custom Roblox fishing game. Tracks the bobber and detects the cast-ready cue.`
- **Topics:** `python`, `windows`, `roblox`, `fishing-game`, `screen-detection`

The repository is small and contains the Python source and setup instructions. The README explains how to download Python, install the packages, and start the helper. The packaged `.exe` is not needed.

## From the Zenon folder in GitHub Desktop

The project folder already has its README and `.gitignore`. To add it from GitHub Desktop:

1. Click **Add an Existing Repository from your local drive…** on the start screen.
2. Click **Choose…** and select the Zenon project folder (the folder containing `fishing_helper.py` and `README.md`).
3. Click **Add Repository**. If it says the folder is not a Git repository yet, cancel and choose **Create a New Repository on your local drive…** instead. Set the name to `zenon-fishing-helper`, and set **Local path** to the folder *above* the existing Zenon folder. If it warns that the folder already exists or isn’t empty, cancel and ask for help before continuing.
4. Once the repository opens, GitHub Desktop will show the files to include. Enter a summary such as `Add Zenon fishing helper`, then click **Commit to main**.
5. Click **Publish repository** at the top. Use the description above. Uncheck **Keep this code private** if anyone should be able to view and download it, then click **Publish repository**.
6. To get the share link, choose **Repository → View on GitHub**. The README appears on the repository page and includes the Python setup tutorial.

The `.gitignore` skips the executable, generated build folders, and ZIP packages, so the Python project stays small. A GitHub Release is not needed to share this source version.
