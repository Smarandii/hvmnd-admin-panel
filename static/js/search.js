document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('searchInput');

    searchInput.addEventListener('keyup', function(event) {
        clearTimeout(window.searchTimer);
        window.searchTimer = setTimeout(function() {
            document.getElementById('searchForm').submit();
        }, 500); // Adjust the timeout to suit how quickly the search triggers
    });
});
