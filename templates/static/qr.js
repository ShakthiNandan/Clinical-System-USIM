document.getElementById('qrscan').addEventListener('submit', function (event) {
    event.preventDefault();
    const imageInput = document.getElementById('image');
    const capturedImage = document.getElementById('capturedImage').src;
    imageInput.value = capturedImage;
    this.submit();
  });


  const video = document.getElementById('video');
  const canvas = document.getElementById('canvas');
  const captureButton = document.getElementById('capture');
  const capturedImage = document.getElementById('capturedImage');

  // Get access to the camera
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true }).then(function (stream) {
      video.srcObject = stream;
      video.play();
    });
  }

  const captureBtn = document.getElementById('capture-btn');
  const errorMessage = document.getElementById('error-message');
  
  captureBtn.addEventListener('click', function() {
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(function(blob) {
        const formData = new FormData();
        formData.append('file', blob, 'capture.png');
  
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            let resultDiv = document.getElementById('result');
            if (data.error) {
                resultDiv.innerHTML = `<p class="error-message">Error: ${data.error}</p>`;
            } else {
                resultDiv.innerHTML = `
                    <a href="${data.data}" target="_blank">${data.data}</a>
                    <button onclick="window.open('${data.data}', '_blank')">Open Link</button>
                `;
            }
        })
        .catch(error => console.error('Error:', error));
    });
  });
  
  document.getElementById('qrscan').addEventListener('submit', function(event) {
    event.preventDefault();
    let formData = new FormData();
    formData.append('file', document.getElementById('file-input').files[0]);
  
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        let resultDiv = document.getElementById('result');
        if (data.error) {
            resultDiv.innerHTML = `<p class="error-message">Error: ${data.error}</p>`;
        } else {
            resultDiv.innerHTML = `
                <a href="${data.data}" target="_blank">${data.data}</a>
                <button onclick="window.open('${data.data}', '_blank')">Open Link</button>
            `;
        }
    })
    .catch(error => console.error('Error:', error));
  });
  
  // Capture photo
  captureButton.addEventListener('click', function () {
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataURL = canvas.toDataURL('image/png');
    capturedImage.src = dataURL;
    capturedImage.style.display = 'block';
  });
