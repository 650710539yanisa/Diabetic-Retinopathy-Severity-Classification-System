// ===== SELECT ELEMENTS =====
const dropArea = document.querySelector(".upload-area");
const fileInput = document.getElementById("img");
const resultBox = document.getElementById("result");
const predictBtn = document.querySelector(".predict-btn");
const loadingOverlay = document.getElementById("loading-overlay");

// ===== INIT STATE =====
resultBox.style.display = "none";

// ===== DRAG EVENTS =====
dropArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropArea.classList.add("drag-over");
});

dropArea.addEventListener("dragleave", () => {
    dropArea.classList.remove("drag-over");
});

dropArea.addEventListener("drop", (e) => {
    e.preventDefault();
    dropArea.classList.remove("drag-over");

    const file = e.dataTransfer.files[0];
    if (!file) return;

    fileInput.files = e.dataTransfer.files;
    previewFile(file);
    showPlaceholder();
});

// ===== CLICK TO OPEN FILE CHOOSER =====
dropArea.addEventListener("click", () => fileInput.click());

// ===== PREVIEW IMAGE =====
fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
        previewFile(file);
        showPlaceholder();
    }
});

function previewFile(file) {
    const img = document.getElementById("preview");
    const container = document.getElementById("preview-container");
    img.src = URL.createObjectURL(file);
    container.style.display = "block";
}

function showPlaceholder() {
    resultBox.style.display = "block";
    resultBox.innerHTML = "Processing not started — Click “Predict”.";
}

// ===== CLEAR IMAGE =====
function clearImage() {
    fileInput.value = "";
    document.getElementById("preview-container").style.display = "none";
    document.getElementById("preview").src = "";
    resultBox.style.display = "none";
}

function selectModel(modelName){

    const hn = document.getElementById("patient-hn").value;

    fetch("/api/doctor_choice", {
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            hn:hn,
            model:modelName
        })
    })
    .then(res=>res.json())
    .then(data=>{
        alert("Doctor selected: " + modelName);
    })
}
// ===== SEND IMAGE (WITH LOADING + HN) =====
function sendImage() {

    const fileInput = document.getElementById("img");
    const loadingOverlay = document.getElementById("loading-overlay");
    const resultBox = document.getElementById("result");
    const predictBtn = document.querySelector(".predict-btn");

    const file = fileInput.files[0];

    if (!file) {
        alert("Please upload an image");
        return;
    }

    // ✅ HN
    const hn = document.getElementById("patient-hn").value;

    if (!hn) {
        alert("No patient HN found");
        return;
    }

    // ✅ eye
    const eye = document.querySelector('input[name="eye"]:checked');

    if (!eye) {
        alert("Please select Left / Right eye");
        return;
    }

    const formData = new FormData();

    formData.append("image", file);
    formData.append("eye", eye.value.toUpperCase());
    formData.append("hn", hn);   // ⭐ สำคัญสุด


    // ===== SHOW LOADING =====
    loadingOverlay.style.display = "flex";
    predictBtn.disabled = true;
    predictBtn.innerText = "Predicting…";


    fetch("/api/predict", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {

        console.log("RESULT:", data);

        // ===== SHOW RESULT =====

        let html = `
            <b>${data.best.label}</b><br>
            Prediction Probability (%): ${(data.best.conf * 100).toFixed(2)}%
            <hr>
            <table style="width:100%">
            <tr>
            <th>Model</th>
            <th>Result</th>
            <th>Prediction Probability (%)</th>
            <th>Doctor Choice</th>
            </tr>
        `;

        data.rows.forEach(r => {
            html += `
                <tr>
                    <td>${r.model}</td>
                    <td>${r.label}</td>
                    <td>${(r.conf * 100).toFixed(2)}%</td>
                    <td>
                        <button onclick="selectModel('${r.model}')">
                            Select
                        </button>
                    </td>
                </tr>
            `;
        });

        html += "</table>";

        resultBox.innerHTML = html;

    })
    .catch(err => {
        console.error(err);
        alert("Prediction failed");
    })
    .finally(() => {

        // ===== HIDE LOADING =====
        loadingOverlay.style.display = "none";
        predictBtn.disabled = false;
        predictBtn.innerText = "Predict";
    });
}


// ===== EXPOSE FUNCTIONS =====
window.sendImage = sendImage;
window.clearImage = clearImage;
window.selectModel = selectModel;
