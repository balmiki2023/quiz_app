
const GITHUB_API =
    "https://api.github.com/repos/quizappofficial/quiz_app/releases/tags/v1.0.0";

async function loadDownloads() {
    const windowsButton = document.getElementById("windows-download");
    const androidButton = document.getElementById("android-download");

    // Disable buttons until download links are loaded.
    windowsButton.removeAttribute("href");
    androidButton.removeAttribute("href");

    windowsButton.textContent = "Loading...";
    androidButton.textContent = "Loading...";

    try {
        const response = await fetch(GITHUB_API);

        if (!response.ok) {
            throw new Error("Release information unavailable.");
        }

        const release = await response.json();
        const assets = release.assets || [];

        const windowsFile = assets.find(asset =>
            asset.name.toLowerCase().endsWith(".exe")
        );

        const androidFile = assets.find(asset =>
            asset.name.toLowerCase().endsWith(".apk")
        );

        if (windowsFile) {
            windowsButton.href = windowsFile.browser_download_url;
            windowsButton.textContent = "Download for Windows";
        } else {
            windowsButton.textContent = "Windows unavailable";
            windowsButton.classList.add("disabled");
        }

        if (androidFile) {
            androidButton.href = androidFile.browser_download_url;
            androidButton.textContent = "Download APK";
        } else {
            androidButton.textContent = "Android unavailable";
            androidButton.classList.add("disabled");
        }

    } catch (error) {
        console.error(error);

        windowsButton.textContent = "Download unavailable";
        androidButton.textContent = "Download unavailable";

        windowsButton.classList.add("disabled");
        androidButton.classList.add("disabled");
    }
}

loadDownloads();
