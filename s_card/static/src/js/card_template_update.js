document.addEventListener('DOMContentLoaded', function () {
    showSection('introduce-section');
});

function addNewImage(containerId, entryClass) {
    var container = document.getElementById(containerId);
    var entryCount = container.getElementsByClassName(entryClass).length;
    var newEntryCount = entryCount + 1;

    var newEntry = document.createElement('div');
    newEntry.innerHTML = `
        <div class="image-entry" style="display: flex;align-items: center;">
            <input type="file" name="image_${newEntryCount}" class="my-2" style="flex: 1;" accept="image/*"/>
            <button type="button" class="btn btn-close btn-sm" style="margin-left: 10px;" aria-label="Close"
                    onclick="removeImage(this)">x
            </button>
        </div>
    `;
    container.appendChild(newEntry);
}

function toggleDeleteButton() {
    var checkboxes = document.querySelectorAll('.image-checkbox');
    var deleteButton = document.getElementById('deleteButton');
    var isChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);
    deleteButton.disabled = !isChecked;
}

document.querySelectorAll('.image-checkbox').forEach(function(checkbox) {
    checkbox.addEventListener('change', toggleDeleteButton);
});

function removeImage(button) {
    var entry = button.closest('.image-entry');
    if (entry) {
        entry.remove();
    }
}

function showSection(sectionId) {
    document.querySelectorAll('section').forEach(section => {
        section.classList.add('hidden');
    });

    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.remove('hidden');
    }
}

var header = document.getElementById("pr-subnav");
if (header) {
    var btns = header.getElementsByClassName("subnav");
    for (var i = 0; i < btns.length; i++) {
        btns[i].addEventListener("click", function () {
            var current = document.getElementsByClassName("active");
            current[0].className = current[0].className.replace(" active", "");
            this.className += " active";
        });
    }
}

function attachEventListeners() {
    var updateInfoBtn = document.getElementById('update-info-btn');
    if (updateInfoBtn) {
        updateInfoBtn.addEventListener('click', function () {
            var cardId = this.getAttribute('card_id');
            updateInformation(cardId);
        });
    }

    var updateIntroBtn = document.getElementById('update-intro-btn');
    if (updateIntroBtn) {
        updateIntroBtn.addEventListener('click', function () {
            var cardId = this.getAttribute('card_id');
            updateIntroduction(cardId);
        });
    }

    var addImageBtn = document.getElementById('add-image-btn');
    if (addImageBtn) {
        addImageBtn.addEventListener('click', function () {
            var cardId = this.getAttribute('card_id');
            addNewImages(cardId);
        });
    }
}

function updateInformation(cardId) {
    var formData = new FormData(document.getElementById('edit-info-form'));
    fetch('/card/infor/' + cardId, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'Success') {
            setTimeout(function() {
                location.reload();
            }, 1000);
        } else {
            alert('Update failed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error during update:', error);
    });
}


function updateIntroduction(cardId) {
    var formData = new FormData(document.getElementById('edit-intro-form'));
    fetch('/card/intro/' + cardId, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'Success') {
            setTimeout(function() {
                location.reload();
            }, 1000);
        } else {
            alert('Update failed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error during update:', error);
    });
}

function validateImageInputs() {
    var imageInputs = document.querySelectorAll('.image-entry input[type="file"]');
    var isValid = true;

    imageInputs.forEach(function (input) {
        if (!input.files.length) {
            isValid = false;
            return;
        }
    });

    if (!isValid) {
        alert('Please select an image file for each input.');
    }

    return isValid;
}

function addNewImages(cardId) {
    var formData = new FormData(document.getElementById('add-image-form'));

    if (!validateImageInputs()) {
        return;
    }

    fetch('/card/image/' + cardId, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'Success') {
            setTimeout(function() {
                location.reload();
            }, 1000);
        } else {
            alert('Add image failed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error during add:', error);
    });
}

function displaySelectedImage(event, elementId) {
    const selectedImage = document.getElementById(elementId);
    const fileInput = event.target;

    if (fileInput.files && fileInput.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            selectedImage.src = e.target.result;
        };
        reader.readAsDataURL(fileInput.files[0]);
    }
}

function checkFileInputs() {
    var fileInputs = document.querySelectorAll('input[type="file"]');
    var addButton = document.getElementById('add-image-btn');
    var hasData = Array.from(fileInputs).some(input => input.files.length > 0);
    addButton.disabled = !hasData;
}

function downloadQRCode() {
    const qrCodeImage = document.getElementById('qrCodeImage');
    const downloadLink = document.createElement('a');
    downloadLink.href = qrCodeImage.src;
    downloadLink.download = 'qr_code.png';
    downloadLink.click();
}

var currentActiveTab = null;

function addActiveClass(element) {
  if (currentActiveTab !== null) {
    currentActiveTab.classList.remove('active');
  }
  element.classList.add('active');
  currentActiveTab = element;
}
attachEventListeners();
