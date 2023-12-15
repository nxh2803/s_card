document.addEventListener('DOMContentLoaded', function () {
    var addButton = document.getElementById('add-contact');
    var followButton = document.getElementById('add-follow');
    var currentPageUrl = window.location.href;

    if (addButton) {
        addButton.addEventListener('click', function () {
            var cardId = addButton.getAttribute('card_id');
            var dynamicHref = '/vcf/' + cardId;
            location.href = dynamicHref;
        });
    }

    if (followButton) {
        followButton.addEventListener('click', function () {
            var user_id = followButton.getAttribute('user_id');
            console.log(user_id);

            fetch('/follow/' + user_id, {
                method: 'POST',
                body: 'user_id=' + user_id,
            })
            .then(function (response) {
                if (response.status === 401) {
                    sessionStorage.setItem('currentPageUrl', currentPageUrl);

                    var loginUrl = '/web/login';
                    window.open(loginUrl, '_blank');
                } else if (response.status === 404) {
                    alert('Card not found for the current user');
                } else if (response.status === 200) {
                    alert('User is now following card');
                }
            })
            .catch(function (error) {
                console.error('There was a problem with the fetch operation:', error.message);
            });
        });
    }
    const showContactButton = document.getElementById('show-contact');

    showContactButton.addEventListener('click', function() {
        const userId = this.getAttribute('user_id');
        loadFollowers(userId);
    });
});

function loadFollowers(userId) {
    fetch(`/followers/${userId}`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            updateFollowerList(data.followers);
        } else {
            console.error('API Error:', data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
}

function updateFollowerList(followersData) {
    const listContainer = document.getElementById('follower-list');
    listContainer.innerHTML = '';

    const ul = document.createElement('ul');
    Object.values(followersData).forEach(follower => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = follower.url;
        link.textContent = `${follower.name} - ${follower.title} at ${follower.company}`;
        link.target = "_blank";

        li.appendChild(link);
        ul.appendChild(li);
    });

    listContainer.appendChild(ul);
}

function deleteSelectedImages() {
    var selectedImageIds = [];
    var checkboxes = document.querySelectorAll('.image-checkbox:checked');

    checkboxes.forEach(function(checkbox) {
        selectedImageIds.push(checkbox.id);
    });
    console.log(selectedImageIds)

    if (selectedImageIds.length > 0) {
        console.log('Deleting images with IDs:', selectedImageIds);
        fetch('/card/image/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ imageIds: selectedImageIds }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            setTimeout(function() {
                location.reload();
            }, 0);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    } else {
        console.log('No images selected');
    }
}

document.getElementById('deleteButton').addEventListener('click', deleteSelectedImages);

function openFileInput() {
    document.getElementById('fileInput').click();
}

function handleFileSelect(event) {
    var file = event.target.files[0];
    if (!file) {
        return;
    }

    var reader = new FileReader();
    reader.onload = function(loadEvent) {
        // Create a new div for the image container
        var newImageContainer = document.createElement('div');
        newImageContainer.id = 'image-container';

        // Add the new image inside a label
        newImageContainer.innerHTML = `
            <div class="image" style="position: relative;display: inline-block;">
                <label>
                    <img src="${loadEvent.target.result}" alt="Uploaded Image" style="width:100%; height: auto; object-fit:cover; border-radius: 4px; max-width: 200px; max-height: 200px;"/>
                </label>
            </div>
        `;

        // Assuming the direct parent of all image containers is the element with class 'uk-grid'
        var parentElement = document.querySelector('.uk-grid-image');
        parentElement.appendChild(newImageContainer);
    };

    reader.readAsDataURL(file);
}


