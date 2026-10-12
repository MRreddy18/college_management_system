// ===============================
// COLLEGE MANAGEMENT JAVASCRIPT
// ===============================


// Confirm before deleting

function confirmDelete() {

    return confirm(
        "Are you sure you want to delete this record?"
    );

}


// Automatically set today's date
// for date inputs

document.addEventListener("DOMContentLoaded", function () {

    const dateInputs =
        document.querySelectorAll(
            'input[type="date"]'
        );

    const today =
        new Date().toISOString().split("T")[0];

    dateInputs.forEach(function(input) {

        if (!input.value) {
            input.value = today;
        }

    });

});