async function uploadAudio() {
    const fileInput = document.getElementById('audioUpload');

    if (!fileInput.files[0]) {
        alert("Upload a file first!");
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    document.getElementById('output').innerText = "⏳ Processing...";

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();

    console.log("RESPONSE:", data);
    document.getElementById('output').innerText = data.text;
}
document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("audioUpload");
    const fileText = document.getElementById("fileName");
    const audioPlayer = document.getElementById("audioPlayer");

    fileInput.addEventListener("change", function () {
        if (this.files.length > 0) {
            const file = this.files[0];

            fileText.innerText = "Selected: " + file.name;

            // 🎧 Create preview URL
            const audioURL = URL.createObjectURL(file);

            audioPlayer.src = audioURL;
            audioPlayer.style.display = "block";
        } else {
            fileText.innerText = "No file selected";
            audioPlayer.style.display = "none";
        }
    });
});
function goToHistory() {
    window.location.href = "/history-page";
}
function downloadText() {
    const text = document.getElementById("output").innerText;

    if (!text || text === "⏳ Processing...") {
        alert("No transcript available!");
        return;
    }

    const blob = new Blob([text], { type: "text/plain" });
    const link = document.createElement("a");

    link.href = URL.createObjectURL(blob);
    link.download = "medical_transcript.txt";
    link.click();
}

