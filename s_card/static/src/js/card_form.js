function validateSocialName(inputElement) {
    var validSocialNames = ['facebook', 'zalo', 'twitter', 'linkedin', 'instagram', 'tiktok', 'pinterest', 'snapchat', 'whatsapp', 'telegram', 'youtube', 'reddit', 'spotify', 'soundcloud', 'twitch', 'github', 'gitlab', 'stackoverflow'];
    var inputValue = inputElement.value.toLowerCase();

    if (validSocialNames.includes(inputValue)) {
        var warningElement = inputElement.parentElement.querySelector('.social-warning');
        if (warningElement) {
            inputElement.parentElement.removeChild(warningElement);
        }
    } else {
        var warningElement = inputElement.parentElement.querySelector('.social-warning');
        if (!warningElement) {
            warningElement = document.createElement('div');
            warningElement.className = 'social-warning';
            warningElement.style.color = 'red';
            warningElement.textContent = 'Please enter the correct social network name.';
            inputElement.parentElement.appendChild(warningElement);
        }
    }
}

function addEntry(containerId, entryClass, namePrefix, addressPrefix, labelName, labelAddress, placeholderAddress, placeholderName) {
    var container = document.getElementById(containerId);
    var entryCount = container.getElementsByClassName(entryClass).length;
    console.log(entryCount)
    var newEntryCount = entryCount + 1;

    var newEntry = document.createElement('div');

    newEntry.innerHTML = `
        <div class="${entryClass}"
            style="background-color: #f2f2f2; padding: 10px; border-radius: 10px;position: relative;margin-top:20px">
            <div style="display: flex; justify-content: center; margin: 8px 0px;">
                <label class="col-sm-auto col-md-10 col-10">
                    ${labelAddress} ${newEntryCount} *
                </label>
            </div>
            <div class="form-group col-md-1 col-1 d-flex justify-content-center align-items-center">
                <button type="button" class="btn btn-close btn-sm"
                        style="position: absolute; top: 20px; right: 20px; transform: translate(50%, -50%); color: red;"
                        aria-label="Close"
                        onclick="removeEntry(this, '${containerId}')">
                </button>
            </div>
            <div class="entry-inputs" style="margin-bottom: 30px; display: flex; justify-content: center;">
                <div class="form-group col-md-10 col-10">
                    <label class="col-sm-auto" style="width: 200px; font-size: 14px; color: #999;">${labelName}:
                    </label>
                    <input type="text" name="${namePrefix}_${newEntryCount}" class="form-control my-2"
                           placeholder="${placeholderName}" required="True"/>
                    <label class="col-sm-auto" style="width: 200px; font-size: 14px; color: #999;">${labelAddress}:
                    </label>
                    <input type="text" name="${addressPrefix}_${newEntryCount}" class="form-control my-2"
                           placeholder="${placeholderAddress}" required="True"/>
                </div>
            </div>
        </div>
    `;
    container.appendChild(newEntry);
}

function addAddressEntry(containerClass, containerId, entryClass, namePrefix, socialPrefix, labelName, labelSocial, placeholderSocial, placeholderName) {
    var entryContainers = document.getElementsByClassName(containerClass);
    var lastContainer = entryContainers[entryContainers.length - 1];
    var lastContainerId = entryContainers.length;

    var newEntryCount = lastContainerId + 1;
    var newEntryName = 'new';

    var newEntry = document.createElement('div');

    newEntry.innerHTML = `
        <div class="${containerClass}" id="socialContainer"
             data-entry-class="social-entry"
             style="clear: both;">
            <div class="${entryClass}" style="background-color: #f2f2f2; padding: 10px; border-radius: 10px;position: relative;margin-bottom: 10px;">
                <div style="display: flex;justify-content: center;">
                    <label class="col-md-12 col-12">
                        ${labelSocial} ${newEntryName} *
                    </label>
                    <div class="form-group col-md-1 col-1 d-flex justify-content-center align-items-center">
                        <button type="button" class="btn btn-close btn-sm"
                                style="position: absolute; top: 8px; right: 26px; transform: translate(50%, -50%); color: red;"
                                onclick="removeAddressEntry(this, '${containerId}')">
                            x
                        </button>
                    </div>
                </div>
                <div class="entry-inputs row" style="display: flex;justify-content: center;">
                    <div class="form-group col-md-12 s_col_no_bgcolor">
                        <div class="col-sm">
                            <input type="text" class="form-control" name="${namePrefix}_${newEntryCount}" placeholder="${placeholderName}" required="True"/>
                        </div>
                    </div>
                    <div class="form-group col-md-12 s_col_no_bgcolor">
                        <div class="col-sm">
                            <input type="text" name="${socialPrefix}_${newEntryCount}" class="form-control" placeholder="${placeholderSocial}" required="True"/>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    lastContainer.appendChild(newEntry);
}

function removeEntry(button, containerId) {
    var entry = button.closest('.globe-entry, .social-entry, .link-entry');
    if (entry) {
        entry.remove();
        updateLabels(containerId);
    }
}

function removeAddressEntry(button, containerId) {
    var entry = button.closest('.globe-entry, .social-entry, .link-entry');
    if (entry) {
        entry.remove();
        updateLabels(containerId);
    }
}

function updateLabels(containerId) {
    var container = document.getElementById(containerId);
    var entries = container.querySelectorAll('.globe-entry, .social-entry, .link-entry');

    entries.forEach(function (entry, index) {
        var labels = entry.querySelectorAll('.col-sm-auto.col-md-10.col-10');
        if (labels.length > 0) {
            labels[0].innerText = labels[0].innerText.replace(/\d+/, index + 1);
        }
    });
}

function addImage(containerId, entryClass) {
    var container = document.getElementById(containerId);
    var entryCount = container.getElementsByClassName(entryClass).length;
    var newEntryCount = entryCount + 1;

    var newEntry = document.createElement('div');
    newEntry.innerHTML = `
        <div class="image-entry">
            <input type="file" name="image_${newEntryCount}" class="my-2" accept="image/*"/>
            <button type="button" class="btn btn-close btn-sm" aria-label="Close" onclick="removeImage(this)">
            </button>
        </div>
    `;
    container.appendChild(newEntry);
}

function removeImage(button) {
    var entry = button.closest('.image-entry');
    if (entry) {
        entry.remove();
    }
}


