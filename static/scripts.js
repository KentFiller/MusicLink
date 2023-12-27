document.addEventListener('DOMContentLoaded', function() {
    // Hide the flash message alert on page load
    const flashMessageAlert = document.getElementById('flash-message-alert');
    flashMessageAlert.style.display = 'none';

    function displayFlashMessage() {
        const flashMessages = document.querySelectorAll('.flash-message');

        if (flashMessages.length > 0) {
            // Show the flash message alert if there are messages to display
            flashMessageAlert.style.display = 'block';

            let currentIndex = 0;

            function displayNextMessage() {
                if (currentIndex < flashMessages.length) {
                    flashMessages[currentIndex].style.display = 'block';
                    setTimeout(function() {
                        flashMessages[currentIndex].style.display = 'none';
                        currentIndex++;
                        displayNextMessage();
                    }, 3000); // Adjust the duration (in milliseconds) for how long each message stays visible
                } else {
                    // Hide the flash message alert when all messages are displayed
                    flashMessageAlert.style.display = 'none';
                }
            }

            displayNextMessage(); // Start displaying flash messages
        }
    }

    displayFlashMessage(); // Start displaying flash messages
});

function toggleCheckboxes(selectAllCheckbox) {
    const checkboxes = document.querySelectorAll('input[name="selected_songs"]');
    const isChecked = selectAllCheckbox.checked;

    checkboxes.forEach((checkbox) => {
        checkbox.checked = isChecked;
    });
}

const individualCheckboxes = document.querySelectorAll('input[name="selected_songs"]');
individualCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', function () {
        // Check if all individual checkboxes are checked
        const allChecked = Array.from(individualCheckboxes).every((cb) => cb.checked);

        // Update the "Select All" checkbox based on the state of individual checkboxes
        document.getElementById('select-all').checked = allChecked;
    });
});

// Function to enable or disable the submit button based on checkbox selection
function toggleSubmitButton() {
    const checkboxes = document.querySelectorAll('input[name="selected_songs"]');
    const submitButton = document.getElementById('download-button');

    let atLeastOneChecked = false;

    checkboxes.forEach((checkbox) => {
        if (checkbox.checked) {
            atLeastOneChecked = true;
            return;
        }
    });

    submitButton.disabled = !atLeastOneChecked;
}

// Add an event listener to the checkboxes
const checkboxes = document.querySelectorAll('input[name="selected_songs"]');
checkboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', toggleSubmitButton);
});

document.addEventListener('DOMContentLoaded', function() {
    const downloadButton = document.getElementById('download-button');

    downloadButton.addEventListener('click', function(e) {
        const selectedSongs = document.querySelectorAll('input[name="selected_songs"]:checked');
        if (selectedSongs.length === 0) {
            // Show the popover if no songs are selected
            downloadButton.setAttribute('data-content', 'Please select at least one song for download');
            $(downloadButton).popover('show');
            e.preventDefault(); // Prevent form submission
        }
    });
});

