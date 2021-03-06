/*
    Important things to note: 
    
    - The edition grid is the physical grid that the user sees on the webpage.
    The data grid (the grid listed under Internal state) has the grid objects and those are what is being
    changed internally

    - jqGrid is the edition grid

    - .ui-selected is automatically added to something that is selected

*/

//dummy function
function testForPath() {
    const val = typeof $('.load_task').attr('value');
    console.log(val);
}

// Internal state.
var CURRENT_INPUT_GRID = new Grid(3, 3);
var CURRENT_OUTPUT_GRID = new Grid(3, 3);
var TEST_PAIRS = new Array();
var CURRENT_TEST_PAIR_INDEX = 0;
var COPY_PASTE_DATA = new Array();
// name of the current file
var CURRENT_FILE_NAME = "";
// List of color(s) that were chosen by user on object form
var LIST_OF_COLORS = [];

// contains array that stores the objects of every input canvas
var INPUT_OBJECT_LIST = [];

// Cosmetic.
var EDITION_GRID_HEIGHT = 500;
var EDITION_GRID_WIDTH = 500;
var MAX_CELL_SIZE = 100;

// Set this value to which input you want to start from
var index = 1;

// To establish a local storage system
class LocalStorageService {
  #keys = {
    inputs: "inputs",
  };

  // Constructs storage
  constructor() {
    this.length = 0;
    this.storage = window.localStorage;
  }

  addObjects(object) {
    console.log(object);
    const obj = this.convertValuesObj(object);
    const objects = this.getObjects();
    objects.push(obj);
    this.setObjects(objects);
    this.length++;
  }

  convertValuesObj(object) {
      var obj = object;

      if (obj['bitmap'] === '') {
        obj['bitmap'] = null;
      }

        for(var prop in obj){
            if(obj.hasOwnProperty(prop) && obj[prop] !== null && !isNaN(obj[prop]) && prop !== 'color'){
                obj[prop] = +obj[prop];   
            }
            else if(obj[prop] === 'false' || obj[prop] === 'true') {
                (obj[prop] === 'false') ? obj[prop] = false : obj[prop] = true;
            }
            else if(obj[prop] === 'null') {
                obj[prop] = null;
            }
        }
        if (obj['bitmap'] !== null) {
          var formattedBitmap = JSON.parse(obj['bitmap']);
          console.log(formattedBitmap);
          obj['bitmap'] = formattedBitmap;
        }
    return obj;
  }

  getObjects() {
    return JSON.parse(this.storage.getItem(this.#keys.inputs)) || [];
  }

  setObjects(objects) {
    this.storage.setItem(this.#keys.inputs, JSON.stringify(objects));
  }

  removePerson(objects) {
    const object = this.getObjects();
    const index = object.indexOf(objects);
    object.splice(index, 1);
    this.setObjects(objects);
    this.length--;
  }

  clear() {
    this.storage.clear();
    this.length = 0;
  }
}

const STORAGE = new LocalStorageService();

/**
 * Restarts the output grid
 */
function resetTask() {
  CURRENT_INPUT_GRID = new Grid(3, 3);
  TEST_PAIRS = new Array();
  CURRENT_TEST_PAIR_INDEX = 0;
  $("#task_preview").html("");
  resetOutputGrid();
}

/**
 * Refresh the 'physical' grid with the data grid
 * @param {*} jqGrid The edition grid (the grid that the users see)
 * @param {*} dataGrid The same output grid but represented as a tuple
 */
function refreshEditionGrid(jqGrid, dataGrid) {
  fillJqGridWithData(jqGrid, dataGrid);
  setUpEditionGridListeners(jqGrid);
  fitCellsToContainer(
    jqGrid,
    dataGrid.height,
    dataGrid.width,
    EDITION_GRID_HEIGHT,
    EDITION_GRID_HEIGHT
  );
  initializeSelectable();
}

/**
 * Syncs the current physical grid to the data grid (CURRENT_OUTPUT_GRID)
 */
function syncFromEditionGridToDataGrid() {
  copyJqGridToDataGrid($("#output_grid .edition_grid"), CURRENT_OUTPUT_GRID);
}

/**
 * Syncs the data grad (CURRENT_OUTPUT_GRID) to the 'physical' grid
 */
function syncFromDataGridToEditionGrid() {
  refreshEditionGrid($("#output_grid .edition_grid"), CURRENT_OUTPUT_GRID);
}

/**
 * Obtains the symbol that was selected by the user
 * @returns Symbole (color) that is selected
 */
function getSelectedSymbol() {
  selected = $("#symbol_picker .selected-symbol-preview")[0];
  return $(selected).attr("symbol");
}

/**
 * Sets the edition grid listeners up. Sets it up for the floodfill and edit buttons
 * @param {*} jqGrid The edition grid
 */
function setUpEditionGridListeners(jqGrid) {
  jqGrid.find(".cell").click(function (event) {
    cell = $(event.target); //obtains the cell that user clicked on
    symbol = getSelectedSymbol(); //obtains the color that is currently selected

    mode = $("input[name=tool_switching]:checked").val(); //obtains the mode that the user selected from the input
    if (mode == "floodfill") {
      // If floodfill: fill all connected cells.
      syncFromEditionGridToDataGrid();
      grid = CURRENT_OUTPUT_GRID.grid;
      floodfillFromLocation(grid, cell.attr("x"), cell.attr("y"), symbol);
      syncFromDataGridToEditionGrid();
    } else if (mode == "edit") {
      // Else: fill just this cell.
      setCellSymbol(cell, symbol);
    }
  });
}

/**
 * Removes all objects from list, if any
 */
function resetObjList() {
  $(".obj-list-item").each(function (i, e) {
    $(e).remove();
  });
}

/**
 * Resizes the edition grid (saves anything that was still on the canvas during resizing)??
 */
function resizeOutputGrid() {
  resetObjList();
  size = $("#output_grid_size").val();
  size = parseSizeTuple(size);
  height = size[0];
  width = size[1];

  jqGrid = $("#output_grid .edition_grid");
  syncFromEditionGridToDataGrid();
  dataGrid = JSON.parse(JSON.stringify(CURRENT_OUTPUT_GRID.grid));
  CURRENT_OUTPUT_GRID = new Grid(height, width, dataGrid);
  refreshEditionGrid(jqGrid, CURRENT_OUTPUT_GRID);
}

/**
 * Resets the output grid to a certain size
 */
function resetOutputGrid() {
  syncFromEditionGridToDataGrid();
  CURRENT_OUTPUT_GRID = new Grid(4, 4);
  syncFromDataGridToEditionGrid();
  resizeOutputGrid();
}

/**
 * Copies what was from the input grid to the current output grid
 */
function copyFromInput() {
  syncFromEditionGridToDataGrid();
  CURRENT_OUTPUT_GRID = convertSerializedGridToGridObject(
    CURRENT_INPUT_GRID.grid
  );
  syncFromDataGridToEditionGrid();
  $("#output_grid_size").val(
    CURRENT_OUTPUT_GRID.height + "x" + CURRENT_OUTPUT_GRID.width
  );
}

/**
 * Creates the edition grids (the physical, viewable input/output grids) in the Task Demonstration box
 * @param {*} pairId        The ID number of the pair
 * @param {*} inputGrid     The inputGrid (as represented as a data grid)
 * @param {*} outputGrid    The outputGrid (as represented as a data grid)
 */
function fillPairPreview(pairId, inputGrid, outputGrid) {
  var pairSlot = $("#pair_preview_" + pairId);
  if (!pairSlot.length) {
    // Create HTML for pair. (creates them for the task demonstration box)
    pairSlot = $(
      '<div id="pair_preview_' +
        pairId +
        '" class="pair_preview" index="' +
        pairId +
        '"></div>'
    );
    pairSlot.appendTo("#task_preview");
  }
  // Creates the edition grid view for the input section of the Task Demonstration box if not already there
  var jqInputGrid = pairSlot.find(".input_preview");
  if (!jqInputGrid.length) {
    jqInputGrid = $('<div class="input_preview"></div>');
    jqInputGrid.appendTo(pairSlot);
  }
  // Creates the edition grid view for the output section of the Task Demonstration box if it is not already there
  var jqOutputGrid = pairSlot.find(".output_preview");
  if (!jqOutputGrid.length) {
    jqOutputGrid = $('<div class="output_preview"></div>');
    jqOutputGrid.appendTo(pairSlot);
  }

  fillJqGridWithData(jqInputGrid, inputGrid);
  fitCellsToContainer(jqInputGrid, inputGrid.height+1, inputGrid.width+1, 200, 200);
  fillJqGridWithData(jqOutputGrid, outputGrid);
  fitCellsToContainer(
    jqOutputGrid,
    outputGrid.height + 1,
    outputGrid.width + 1,
    200,
    200
  );
}

/**
 * Loads all the edition grids under Task Demonstration, and also loads the input grid that tests the user
 * @param {*} train From the JSON data (contains the input and output grids)
 * @param {*} test  Contains the testing set (the input grids that the user is supposed to solve)
 */
function loadJSONTask(train, test) {
  resetTask();
  $("#modal_bg").hide(); //hides the introduction page
  $("#error_display").hide();
  $("#info_display").hide();

  // Loads every input/output pairs under Task Demonstration
  for (var i = 0; i < train.length; i++) {
    pair = train[i];
    values = pair["input"];
    input_grid = convertSerializedGridToGridObject(values);
    values = pair["output"];
    output_grid = convertSerializedGridToGridObject(values);
    fillPairPreview(i, input_grid, output_grid);
  }
  for (var i = 0; i < test.length; i++) {
    pair = test[i];
    TEST_PAIRS.push(pair);
  }
  values = TEST_PAIRS[0]["input"]; //is there an output section?
  CURRENT_INPUT_GRID = convertSerializedGridToGridObject(values);
  fillTestInput(CURRENT_INPUT_GRID);
  CURRENT_TEST_PAIR_INDEX = 0;
  $("#current_test_input_id_display").html("1");
  $("#total_test_input_count_display").html(test.length);
}

/**
 * Displays the name of the task
 * @param {String} task_name        Name of task
 * @param {Number} task_index       What number task
 * @param {Number} number_of_tasks  How many tasks there
 */
function display_task_name(task_name, task_index, number_of_tasks) {
  CURRENT_FILE_NAME = task_name;
  big_space = "&nbsp;".repeat(4);
  document.getElementById("task_name").innerHTML =
    "Task name:" +
    // big_space +
    task_name +
    // big_space +
    (task_index === null
      ? ""
      : String(task_index) + " out of " + String(number_of_tasks));
}

/**
 * To load the task after the user selects a file from their computer
 * @param {*} e The event of the user selecting a file
 * @returns
 */
function loadTaskFromFile(e) {
  var file = e.target.files[0];
  if (!file) {
    errorMsg("No file selected");
    return;
  }
  var reader = new FileReader();

  //For when the reader is reading the file
  reader.onload = function (e) {
    var contents = e.target.result;

    try {
      contents = JSON.parse(contents);
      train = contents["train"];
      test = contents["test"];
    } catch (e) {
      errorMsg("Bad file format");
      return;
    }
    loadJSONTask(train, test);

    //$("#load_task_file_input")[0].value = "";
    display_task_name(file.name, null, null);
  };

  reader.readAsText(file);
}

/**
 * Displays a task when the user hits the "Start task from ..." button in the intro
 */
function randomTask() {
  var subset = "training";
  $.getJSON(
    "https://api.github.com/repos/fchollet/ARC/contents/data/" + subset,
    function (tasks) {
      var task_index = index; //Math.floor(Math.random() * tasks.length)  <-- this is to set what tasks should be loaded first
      var task = tasks[task_index];
      index++; // ??

      // Try to load the grids from the file
      $.getJSON(task["download_url"], function (json) {
        try {
          train = json["train"];
          test = json["test"];
        } catch (e) {
          errorMsg("Bad file format");
          return;
        }

        loadJSONTask(train, test);
        //$('#load_task_file_input')[0].value = "";

        infoMsg("Loaded task training/" + task["name"]);
        display_task_name(task["name"], task_index, tasks.length);
        $('.current-input').text(JSON.stringify([{}], null, 4));
        $('.overall-json').text(JSON.stringify([], null, 4));
      }).error(function () {
        errorMsg("Error loading task");
      });
    }
  ).error(function () {
    errorMsg("Error loading task list");
  });
}

/**
 * Loads the next test input onto the input grid
 * @returns
 */
function nextTestInput() {
  if (TEST_PAIRS.length <= CURRENT_TEST_PAIR_INDEX + 1) {
    errorMsg("No next test input. Pick another file?");
    return;
  }
  CURRENT_TEST_PAIR_INDEX += 1;
  values = TEST_PAIRS[CURRENT_TEST_PAIR_INDEX]["input"];
  CURRENT_INPUT_GRID = convertSerializedGridToGridObject(values); //serializedgrid is actually the array representation??
  fillTestInput(CURRENT_INPUT_GRID);
  $("#current_test_input_id_display").html(CURRENT_TEST_PAIR_INDEX + 1);
  $("#total_test_input_count_display").html(test.length);
}

/**
 * Compares the output grid to the correct solution to see if the solution is correct
 * @returns
 */
function submitSolution() {
  syncFromEditionGridToDataGrid();

  //Referential output in the data that the gui compares it to
  reference_output = TEST_PAIRS[CURRENT_TEST_PAIR_INDEX]["output"];
  submitted_output = CURRENT_OUTPUT_GRID.grid;
  if (reference_output.length != submitted_output.length) {
    errorMsg("Wrong solution.");
    return;
  }
  for (var i = 0; i < reference_output.length; i++) {
    ref_row = reference_output[i];
    for (var j = 0; j < ref_row.length; j++) {
      if (ref_row[j] != submitted_output[i][j]) {
        errorMsg("Wrong solution.");
        return;
      }
    }
  }
  infoMsg("Correct solution!");
}

/**
 * Fills in the input grid (test input grid)
 * @param {*} inputGrid The input Grid object
 */
function fillTestInput(inputGrid) {
  jqInputGrid = $("#evaluation_input");
  fillJqGridWithData(jqInputGrid, inputGrid);
  fitCellsToContainer(jqInputGrid, inputGrid.height+1, inputGrid.width+1, 400, 400);
}

/**
 * Copies pixels from the input grid to the output grid
 */
function copyToOutput() {
  syncFromEditionGridToDataGrid();
  CURRENT_OUTPUT_GRID = convertSerializedGridToGridObject(
    CURRENT_INPUT_GRID.grid
  );
  syncFromDataGridToEditionGrid();
  $("#output_grid_size").val(
    CURRENT_OUTPUT_GRID.height + "x" + CURRENT_OUTPUT_GRID.width
  );
}

//initializes jQuery selectable
//makes the grid selectable (allows to select multiple cells)
function initializeSelectable() {
  $("#add_object_btn").hide();
  $("#remove_object_btn").hide();

  try {
    $(".selectable_grid").selectable("destroy");
  } catch (e) {}
  //:checked means if the radio button was selected for the tool
  toolMode = $("input[name=tool_switching]:checked").val();
  if (toolMode == "select") {
    infoMsg("Select pixels");
    $(".selectable_grid").selectable({
      autoRefresh: false,
      filter: "> .row > .cell",
      start: function (event, ui) {
        $(".ui-selected").each(function (i, e) {
          $(e).removeClass("ui-selected");
        });
      },
    });
  }

  // When a cell is selected, it has the class .ui-selected or .group-selected
  else if (toolMode == "group") {
    $("#add_object_btn").toggle();
    $("#remove_object_btn").toggle();
    $(".selectable_grid").selectable({
      filter: "> .row > .cell",

      start: function (event, ui) {
        $(".ui-selected").each(function (i, e) {
          $(e).removeClass("ui-selected");
          $(e).addClass("group-selected");
        });
      },

      selected: function (event, ui) {
        $(".ui-selected.group-selected").each(function (i, e) {
          $(e).removeClass("ui-selected");
          $(e).removeClass("group-selected");
        });
      },
    });
  }
}

/**
 * Converts a form to JSON
 * @param {*} form The form that we want to convert to JSON
 * @returns
 */
function convertFormToJSON(form) {
  const array = form.serializeArray();
  console.log(array);
  const json = {};
  $.each(array, function () {
    json[this.name] = this.value || "";
  });
  return json;
}

async function writeSaveFile(json) {
  const str = JSON.stringify(json, null, 4);
  const blob = new Blob([str], {
    type: "application/json",
  });

  const fileHandle = await window.showSaveFilePicker();
  const fileStream = await fileHandle.createWritable();

  await fileStream.write(blob);
  await fileStream.close();

  INPUT_OBJECT_LIST = [];
  $(".overall-json").text(JSON.stringify(INPUT_OBJECT_LIST, null, 4));
}

// To clear local storage when page is refreshed
window.onbeforeunload = function (e) {
  STORAGE.clear();
};

// Initial event binding.

$(document).ready(function () {
  //------------------------------------------------------------------------------
  //this part selects which symbol is picked (which color is picked)
  $(".symbol_picker")
    .find(".symbol_preview")
    .click(function (event) {
      symbol_preview = $(event.target);
      console.log(symbol_preview.parent().prop('className'));

      // This if statement is to handle the logic of the object-form color picker
      if (symbol_preview.parent().prop('className') === 'symbol_picker form-color-picker') {
        symbol_preview.toggleClass('selected-symbol-preview');

        // If the user selects/deselects a color from the form
        if (symbol_preview.hasClass('selected-symbol-preview')) {
          LIST_OF_COLORS.push(parseInt(symbol_preview.attr('symbol')));
        } else {
          var index = LIST_OF_COLORS.indexOf(parseInt(symbol_preview.attr('symbol')));
          LIST_OF_COLORS.splice(index, 1);
        }
      }
      else {
      $(".symbol_picker")
        .find(".symbol_preview.interactive")
        .each(function (i, preview) {
          $(preview).removeClass("selected-symbol-preview");
        });
      symbol_preview.addClass("selected-symbol-preview");
      }
      // -----------------------------------------------------------------------------

      // For when the tool mode is either in select or group
      toolMode = $("input[name=tool_switching]:checked").val();
      if (toolMode == "select") {
        $(".edition_grid")
          .find(".ui-selected")
          .each(function (i, cell) {
            symbol = getSelectedSymbol();
            setCellSymbol($(cell), symbol);
          });
      }
    });

  // Makes the cells of the grid interactive
  $(".edition_grid").each(function (i, jqGrid) {
    setUpEditionGridListeners($(jqGrid));
  });

  // For when the user selects a file
  $(".load_task").on("change", function (event) {
    loadTaskFromFile(event);
  });

  $(".load_task").on("click", function (event) {
    //event.target.value = "";
  });

  // Attaching the event listener inside
  $(".object-list").on("click", ".an-object", function (e) {
    $(`.object-${this.value.replace(/\s/g, "")}`).each(function (i, e) {
      var randomColor = Math.floor(Math.random() * 16777215).toString(16);
      $(e).toggleClass(`object-selection`);
    });
    $(this).toggleClass("an-object-selected");
  });

  // When the add object button is clicked
  $("#add_object_btn").on("click", function (e) {
    let nameObj = prompt("Label object");
    let forClass = nameObj.replace(/\s/g, "");
    $(".group-selected, .ui-selected").each(function (i, e) {
      $(e).addClass(`object-${forClass}`);
      $(e).removeClass("group-selected ui-selected");
    });
    $(
      ".object-list"
    ).append(`<li class='list-item-${forClass} obj-list-item'><input type='button' class='an-object' value='${nameObj}' />
            <input type='checkbox' class='remove-obj-check' name='${nameObj}' value='' /></li>`);
  });

  // Attaching event listener to when user wants to remove an object from the list
  $("#remove_object_btn").on("click", function (e) {
    $(".remove-obj-check").each(function (i, e) {
      if ($(e).is(":checked")) {
        obj = $(e).parent();
        obj.remove();
      }
    });
  });

  //Attach even listener to add-obj-labeling form
  $(".submit-form").on("click", function (e) {
    writeSaveFile(INPUT_OBJECT_LIST)
      .then((_) => {
        INPUT_OBJECT_LIST = [];
        $(".overall-json").text(JSON.stringify(INPUT_OBJECT_LIST, null, 4));
      })
      .catch((e) => {
        console.log(e);
        return;
      });
    //console.log(INPUT_OBJECT_LIST);
  });

  // Adds a new object to the local storage
  $(".add-new-obj").on("click", function (e) {
    const form = $(".object-label-form");
    var json = convertFormToJSON(form);
    json['color'] = LIST_OF_COLORS;
    // form[0].reset();
    console.log(json);
    STORAGE.addObjects(json);
    $(".current-input").text(JSON.stringify(STORAGE.getObjects(), null, 4));
  });

  $(".next-input-canvas").on("click", function (e) {
    // checks if the local storage is empty
    // if local storage is empty, then return an empty json object
    if (STORAGE.length === 0) {
      INPUT_OBJECT_LIST.push([{}]);
    } else {
      INPUT_OBJECT_LIST.push(STORAGE.getObjects());
      STORAGE.clear();
      $('.current-input').text(JSON.stringify([{}], null, 4));
    }
    $(".overall-json").text(JSON.stringify(INPUT_OBJECT_LIST, null, 4));
    console.log(JSON.stringify(INPUT_OBJECT_LIST, null, 4));
  });

  $('.clear-json-prev').on('click', function(e) {
    INPUT_OBJECT_LIST = [];
    $('.overall-json').text(JSON.stringify([], null, 4));
  });

  $('.clear-objects-prev').on('click', function(e) {
    STORAGE.clear();
    $('.current-input').text(JSON.stringify([{}], null, 4));
  });

  $("input[type=radio][name=tool_switching]").change(function () {
    initializeSelectable();
  });

  $("input[type=text][name=size]").on("keydown", function (event) {
    if (event.keyCode == 13) {
      resizeOutputGrid();
    }
  });

  $("body").keydown(function (event) {
    // Copy and paste functionality.
    if (event.which == 67) {
      // Press C

      selected = $(".ui-selected");
      if (selected.length == 0) {
        return;
      }

      COPY_PASTE_DATA = [];
      for (var i = 0; i < selected.length; i++) {
        x = parseInt($(selected[i]).attr("x"));
        y = parseInt($(selected[i]).attr("y"));
        symbol = parseInt($(selected[i]).attr("symbol"));
        COPY_PASTE_DATA.push([x, y, symbol]);
      }
      infoMsg(
        "Cells copied! Select a target cell and press V to paste at location."
      );
    }
    if (event.which == 86) {
      // Press P
      if (COPY_PASTE_DATA.length == 0) {
        errorMsg("No data to paste.");
        return;
      }
      selected = $(".edition_grid").find(".ui-selected");
      if (selected.length == 0) {
        errorMsg("Select a target cell on the output grid.");
        return;
      }

      jqGrid = $(selected.parent().parent()[0]);

      if (selected.length == 1) {
        targetx = parseInt(selected.attr("x"));
        targety = parseInt(selected.attr("y"));

        xs = new Array();
        ys = new Array();
        symbols = new Array();

        for (var i = 0; i < COPY_PASTE_DATA.length; i++) {
          xs.push(COPY_PASTE_DATA[i][0]);
          ys.push(COPY_PASTE_DATA[i][1]);
          symbols.push(COPY_PASTE_DATA[i][2]);
        }

        minx = Math.min(...xs);
        miny = Math.min(...ys);
        for (var i = 0; i < xs.length; i++) {
          x = xs[i];
          y = ys[i];
          symbol = symbols[i];
          newx = x - minx + targetx;
          newy = y - miny + targety;
          res = jqGrid.find('[x="' + newx + '"][y="' + newy + '"] ');
          if (res.length == 1) {
            cell = $(res[0]);
            setCellSymbol(cell, symbol);
          }
        }
      } else {
        errorMsg(
          "Can only paste at a specific location; only select *one* cell as paste destination."
        );
      }
    }
  });

  $('textarea').on('keydown', function(e) {
    if (e.key == 'Tab') {
      e.preventDefault();
      var start = this.selectionStart;
      var end = this.selectionEnd;
  
      // set textarea value to: text before caret + tab + text after caret
      this.value = this.value.substring(0, start) +
        "\t" + this.value.substring(end);
  
      // put caret at right position again
      this.selectionStart =
        this.selectionEnd = start + 1;
    }
  });
});
