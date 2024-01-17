$(document).ready(function(){
    $("#searchInput").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $("#userTable tr:not(.header)").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
});

$(document).ready(function(){
    var originalRows = $('#userTable tr').toArray(); // Store the original row order

    $('th').click(function(){
        var table = $(this).parents('table').eq(0);
        var index = $(this).index();
        var rows = table.find('tr:gt(0)').toArray().sort(comparer(index));
        this.asc = !this.asc;
        if (!this.asc) { rows = rows.reverse(); }
        for (var i = 0; i < rows.length; i++) { table.append(rows[i]); }

        $('th').removeClass('sorted-asc sorted-desc');
        $(this).addClass(this.asc ? 'sorted-asc' : 'sorted-desc');
    });

    function comparer(index) {
        return function(a, b) {
            var valA = getCellValue(a, index), valB = getCellValue(b, index);
            return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.localeCompare(valB);
        }
    }

    function getCellValue(row, index) {
        var cell = $(row).children('td').eq(index);
        var input = cell.find('input[type=number]');
        return input.length ? parseFloat(input.val()) : cell.text();
    }

    $('#clearSorting').click(function() {
        $('th').removeClass('sorted-asc sorted-desc');
        var table = $('#userTable');
        $.each(originalRows, function(index, row) {
            table.append(row);
        });
    });
});