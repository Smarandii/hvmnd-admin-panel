document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('searchInput');
    searchInput.focus();
    var val = searchInput.value; // Store the value of the input
    searchInput.value = ''; // Clear the input
    searchInput.value = val; // Set back the value

    searchInput.addEventListener('keyup', function(event) {
        clearTimeout(window.searchTimer);
        window.searchTimer = setTimeout(function() {
            document.getElementById('searchForm').submit();
        }, 500); // Delay for live search
    });
});