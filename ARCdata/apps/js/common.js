/**
 * Class for Grid object; to make a canvas for ARC
 */
 class Grid {
    /**
     * Constructor for a grid object
     * @param {Number} height Height of the canvas
     * @param {Number} width Width of the canvas
     * @param {Number} values Color of the pixel 
     */
    constructor(height, width, values) {
        this.height = height;
        this.width = width;
        this.grid = new Array(height);
        for (var i = 0; i < height; i++){
            this.grid[i] = new Array(width);
            for (var j = 0; j < width; j++){
                if (values != undefined && values[i] != undefined && values[i][j] != undefined){
                    this.grid[i][j] = values[i][j];
                } else {
                    this.grid[i][j] = 0;
                }
            }
        }
    }
}

/**
 * Fills every cell connected to the one the user selects with the selected color
 * @param {*} grid Output grid (Grid object)
 * @param {*} i y coordinate of pixel user selects
 * @param {*} j x coordinate of pixel user selects
 * @param {*} symbol Color that the user selects
 * @returns Grid with color 'flooded' in
 */
function floodfillFromLocation(grid, i, j, symbol) {
    i = parseInt(i);
    j = parseInt(j);
    symbol = parseInt(symbol);

    target = grid[i][j];
    
    if (target == symbol) {
        return;
    }

    /**
     * Colors in the grid after the user selects a pixel using the flood fill option
     * @param {*} i y coordinate
     * @param {*} j x coordinate
     * @param {*} symbol The color that the user wants
     * @param {*} target The color that should be replaced
     */
    function flow(i, j, symbol, target) {
        if (i >= 0 && i < grid.length && j >= 0 && j < grid[i].length) {
            if (grid[i][j] == target) {
                grid[i][j] = symbol;
                flow(i - 1, j, symbol, target);
                flow(i + 1, j, symbol, target);
                flow(i, j - 1, symbol, target);
                flow(i, j + 1, symbol, target);
            }
        }
    }

    flow(i, j, symbol, target);
}

/**
 * Parses the 'change-grid-size' input
 * @param {*} size The string the user inputs to change the grid size (i.e. 3x3, 4x5, etc.)
 * @returns A tuple for the parsed size of the grid
 */
function parseSizeTuple(size) {
    size = size.split('x');
    if (size.length != 2) {
        alert('Grid size should have the format "3x3", "5x7", etc.');
        return;
    }
    if ((size[0] < 1) || (size[1] < 1)) {
        alert('Grid size should be at least 1. Cannot have a grid with no cells.');
        return;
    }
    if ((size[0] > 30) || (size[1] > 30)) {
        alert('Grid size should be at most 30 per side. Pick a smaller size.');
        return;
    }
    return size;
}

/**
 * Converts the serialized grid version (the 2D array representation) to a Grid object
 * @param {*} values The tuple (from parseSizeTuple)
 * @returns Grid object
 */
function convertSerializedGridToGridObject(values) {
    height = values.length;
    width = values[0].length;
    return new Grid(height, width, values)
}

/**
 * Resizes the grid cells so that it fits inside of the container (HTML box)
 * @param {*} jqGrid The output grid
 * @param {*} height Height of the output grid
 * @param {*} width Width of the output grid
 * @param {*} containerHeight The HTML container's height
 * @param {*} containerWidth The HTML container's width
 */
function fitCellsToContainer(jqGrid, height, width, containerHeight, containerWidth) {
    candidate_height = Math.floor((containerHeight - height) / height);
    candidate_width = Math.floor((containerWidth - width) / width);
    size = Math.min(candidate_height, candidate_width);
    size = Math.min(MAX_CELL_SIZE, size);
    jqGrid.find('.cell').css('height', size + 'px');
    jqGrid.find('.cell').css('width', size + 'px');
}

/**
 * Adds color and cells to the jqGrid
 * @param {*} jqGrid The output grid that can be seen by the user
 * @param {*} dataGrid The data version of the grid (probably contains a 2D array of what the actual grid is supposed to look like)
 */
function fillJqGridWithData(jqGrid, dataGrid) {
    jqGrid.empty();
    height = dataGrid.height;
    width = dataGrid.width;
    for (var i = 0; i < height; i++){
        var row = $(document.createElement('div'));
        row.addClass('row');
        // add Y axis tick for each row
        var cell = $(document.createElement('div'));
        cell.addClass('cell');
        cell.addClass('tick');
        cell.text(String(height - i - 1));
        row.append(cell);
        for (var j = 0; j < width; j++){
            var cell = $(document.createElement('div'));
            cell.addClass('cell');
            cell.attr('x', i);
            cell.attr('y', j);
            setCellSymbol(cell, dataGrid.grid[i][j]);
            row.append(cell);
        }
        jqGrid.append(row);
    }
    // render x axis for easier labelling
    var xaxis = $(document.createElement('div'));
    xaxis.addClass('row');
    var cell = $(document.createElement('div')); // dumb placeholder 
    cell.addClass('cell');
    cell.addClass('tick');
    xaxis.append(cell)
    for (var j = 0; j < width; j++){
        var cell = $(document.createElement('div'));
        cell.addClass('cell');
        cell.addClass('tick');
        cell.text(String(j));
        // setCellSymbol(cell, dataGrid.grid[height][j]);
        xaxis.append(cell);
    }
    jqGrid.append(xaxis);
}

function addYAxis(row) {

}

/**
 * Copies the jqGrid (the output grid that the user sees on the HTML) to a data grid (2D array)
 * @param {*} jqGrid The physical grid
 * @param {*} dataGrid The 2D array representation 
 * @returns 
 */
function copyJqGridToDataGrid(jqGrid, dataGrid) {
    row_count = jqGrid.find('.row').length
    if (dataGrid.height != row_count) {
        return
    }
    col_count = jqGrid.find('.cell').length / row_count
    if (dataGrid.width != col_count) {
        return
    }
    jqGrid.find('.row').each(function(i, row) {
        $(row).find('.cell').each(function(j, cell) {
            dataGrid.grid[i][j] = parseInt($(cell).attr('symbol'));
        });
    });
}

/**
 * Sets the color of the cells
 * @param {*} cell Output grid cell
 * @param {*} symbol The color of the cell
 */
function setCellSymbol(cell, symbol) {
    cell.attr('symbol', symbol);
    classesToRemove = ''
    for (i = 0; i < 10; i++) {
        classesToRemove += 'symbol_' + i + ' ';
    }
    cell.removeClass(classesToRemove);
    cell.addClass('symbol_' + symbol);
}

/**
 * Displays an error message
 * @param {*} msg A string
 */
function errorMsg(msg) {
    $('#error_display').stop(true, true);
    $('#info_display').stop(true, true);

    $('#error_display').hide();
    $('#info_display').hide();
    $('#error_display').html(msg);
    $('#error_display').show();
    $('#error_display').fadeOut(5000);
}

/**
 * Displays an informational message for the user
 * @param {*} msg String
 */
function infoMsg(msg) {
    $('#error_display').stop(true, true);
    $('#info_display').stop(true, true);

    $('#info_display').hide();
    $('#error_display').hide();
    $('#info_display').html(msg);
    $('#info_display').show();
    $('#info_display').fadeOut(5000);
}
