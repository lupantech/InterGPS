// Obtain text data //
// $("#id_problem_text").val(data.problem_text);
$("#id_problem_text").val(data.annotat_text); // problem text with latex expressions
$("#id_answer").val(data.answer);
$("#id_comment").val(data.comment);

$('#text').val(logic_forms.text_logic_form.join("\n"))
$('#dissolved').val(logic_forms.dissolved_text_logic_form.join("\n"))
$('#diagram').val(logic_forms.diagram_logic_form.join("\n"))
$('#linein').val(logic_forms.line_instances.sort().join("\n"))
$('#circle').val(logic_forms.circle_instances.join("\n"))

var pointsOptions = document.getElementById("pointsOptions")

function loadPointPositions() {
  var cur = [];
  for (var key in logic_forms.point_positions) {
    cur.push(key + ": " + logic_forms.point_positions[key].join(", "));
  }
  $('#position').val(cur.join("\n"));
}

loadPointPositions();

// Load previous diagram logic forms
$('#load_previous').click(function () {
  if (confirm("Are you sure you want to load previous diagram logic forms?")) {
    console.log(previous_logic_forms)
    $('#diagram').val(previous_logic_forms.diagram_logic_form.join("\n"))
    $('#linein').val(previous_logic_forms.line_instances.sort().join("\n"))
    $('#circle').val(previous_logic_forms.circle_instances.join("\n"))

    var cur = [];
    for (var key in previous_logic_forms.point_positions) {
      for (let i = 0; i < previous_logic_forms.point_positions[key].length; i++)
        previous_logic_forms.point_positions[key][i] = previous_logic_forms.point_positions[key][i].toFixed(0);
      cur.push(key + ": " + previous_logic_forms.point_positions[key].join(", "));
    }
    $('#position').val(cur.join("\n"));

  }
});

// $(".math-input").on("change paste keyup", function (e) { // For 'math-input' element, if change/paste/keyup the value, excute the function()
//     // latex render
//     //katex.render((this).closest('.math-render').children("p").get(0), {
//     //throwOnError: false
//     //});
//     console.log("hi")
//     $(this).closest('.math-render').children("p").html($(this).val());
//     MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
//
// })

for (let i = 0; i < data.choices.length; i++) {
  $('#choice' + (i + 1)).val(data.choices[i]);
}

for (let i = 0; i < data.problem_type_graph.length; i++) {
  value = data.problem_type_graph[i];
  $("#graph").find('input[value=' + value + ']').prop("checked", true);
}

for (let i = 0; i < data.problem_type_goal.length; i++) {
  value = data.problem_type_goal[i];
  $("#goal").find('input[value=' + value + ']').prop("checked", true);
}

// Previous button
if (annot_num === 1) {
  $('#previous').hide();
  $('#load_previous').hide();
}

$('#previous').click(function () {
  if (annot_num != 1) {
    window.location.href = "/edit/" + names[names.length - annot_num + 1];
  }
});

// Next button
if (annot_num === names.length) {
  $('#next').hide();
  $('#submit_and_next').hide();
}

$('#next').click(function () {
  if (annot_num != names.length) {
    window.location.href = "/edit/" + names[names.length - annot_num - 1];
  }
});

// Save and Next button
$('#submit_and_next').click(function (e) {
  document.getElementById('next_name').value = names[names.length - annot_num - 1];
  $("#dataContainer").submit();
});

/////////////////////// Archive functionality ///////////////////////////
// Viewer UI
$('.expand-container').on('click', () => {
  $('#expand-control').toggleClass('rotated');
  $('.viewer').toggleClass('expanded');
  $('.viewer-content').toggleClass('hide');
});

// Archive functionality
num = 5000;
names = undefined;

function update() {
  $('#archive-content').empty();
  result = $.get('/get_list/', function () {
    names = result.responseJSON;
    if (names) {
      let length = num > names.length ? names.length : num;
      for (let i = 0; i < length; i++) {
        $(`<div class="item">
        <p><span class="index">[#` + (names.length - i) + `]</span>
    <span class="name">` + names[i] + `</span></p>
    </div>`).appendTo('#archive-content').click(function () {
          window.location.href = "/edit/" + $(".name", this).text().trim();
        });
      }
    } else {
      $('#archive-content').append('<p>No annotation yet</p>');
    }
    // When creating annotation, no need to highlight
    if (typeof problem_id !== 'undefined') {
      $('.item:contains("' + problem_id + '")').css('background-color', 'orange');
      $('#archive-content').animate({
        scrollTop: $('.item:contains("' + problem_id + '")').offset().top - $('#archive-content').height() / 2
      }, 1000);
    }
  });
}

update();

$('#archive-content').scroll(function () {
  if ($(this).scrollTop() == $(document).height() - $(this).height()) {
    // ajax call get data from server and append to the div
    console.log("bottom");
  }
});

$('#reload').click(function () {
  $("#reload").toggleClass('reload-rotate');
  update();
});


/////////////////////// Submission and Save ///////////////////////////
var problem_text;
var choices = new Array();
var answer;
var problem_type_graph = new Array();
var problem_type_goal = new Array();
var comment;

// Validation function //
function validation() {

  if (problem_text == "") {
    console.log("Error.");
    alert("Error! Please check the Problem Text!");
    return false;
  }

  // validate Choices
  var choices_copy = choices.filter(d => (d && d.length > 0));
  var cnum = choices_copy.length;
  if (cnum == 0 || choices[cnum - 1] != choices_copy[cnum - 1]) {
    alert("Error! Please check the Choices!");
    return false;
  }

  // validate Answer
  var answer_list = ['A', 'B', 'C', 'D'];
  var C = answer_list[cnum - 1];
  var regk = "/^[A-" + C + "]{1}$/"; // reg rule: valid answer must be in ['A','B',...,'C']
  var reg = eval(regk);
  if (!reg.test(answer)) {
    alert("Error! Please check the Answer!");
    return false;
  }

  // validate problem_type_graph
  var valid_num = problem_type_graph.filter(d => d != undefined).length;
  if (valid_num < 1) {
    alert("Error! Please check the Problem Type (Graph)!");
    return false;
  }

  // validate problem_type_goal
  valid_num = problem_type_goal.filter(d => d != undefined).length;
  if (valid_num < 1) {
    alert("Error! Please check the Problem Type (Goal)!");
    return false;
  }

  return true;
}

// Submission function //
function submit_func(e) {

  e.preventDefault();

  problem_text = $("#id_problem_text").val();
  answer = $("#id_answer").val();
  comment = $("#id_comment").val();

  for (var i = 0; i < 8; i++) {
    choices[i] = $("#choice" + (i + 1)).val();
  }

  for (var i = 0; i < 9; i++) {
    id_name = "#typeCheck" + (i + 1) + ":checked"
    problem_type_graph[i] = $(id_name).val();
  }

  for (var i = 0; i < 5; i++) {
    id_name = "#goalCheck" + (i + 1) + ":checked"
    problem_type_goal[i] = $(id_name).val();
  }

  var text_logic_form = $('#text').val().split('\r\n');
  var dissolved_text_logic_form = $('#dissolved').val().split('\r\n');
  var diagram_logic_form = $('#diagram').val().split('\r\n');
  var line_instances = $('#linein').val().split('\r\n');
  var circle_instances = $('#circle').val().split('\r\n');
  var point_positions = $('#position').val().split('\r\n');


  // validate and submit
  if (validation() === true) {
    console.log("validation passed");

    let data = {
      'problem_text': problem_text,
      'answer': answer,
      'comment': comment,
      'problem_type_graph': problem_type_graph,
      'problem_type_goal': problem_type_goal,
      "text_logic_form": text_logic_form,
      "dissolved_text_logic_form": dissolved_text_logic_form,
      "diagram_logic_form": diagram_logic_form,
      "line_instances": line_instances,
      "point_positions": point_positions,
      "circle_instances": circle_instances
    }

    window.localStorage.setItem('data', JSON.stringify(data));
    $(this).unbind('submit').submit();

  } else {
    console.log("validation false");
  }
}

var canvas = document.getElementById("problemCanvas");
var ctx = canvas.getContext("2d");

canvas.addEventListener("mousemove", function (e) {
  findxy('move', e)
}, false);

canvas.addEventListener("mousedown", function (e) {
  findxy('down', e)
}, false);

var currX = 0;
var currY = 0;

var adjx = -1;
var adjy = -1;

function findxy(res, e) {
  currX = e.clientX - canvas.offsetLeft + adjx;
  currY = e.clientY - Math.floor(canvas.getBoundingClientRect().top) + adjy;
  if (res == 'move') {
    // console.log(currX, currY, e.clientX, e.clientY);

  } else if (res == 'down') {
    console.log(currX, currY, e.clientX, e.clientY);

    var selectedPoint = $("#pointsOptions").val();
    if (selectedPoint == null) {
      return;
    }
    logic_forms.point_positions[selectedPoint] = [Math.round(currX / ratio) - data.offset[0], Math.round(currY / ratio) - data.offset[1]]
    drawCanvas();
    loadPointPositions();
  }
}

var image = new Image();
image.src = data.img2;

image.onload = function initCanvas() {
  drawCanvas();
}

function drawImageScaled(ctx, img) {
  let hRatio = ctx.canvas.width / img.width;
  var vRatio = ctx.canvas.height / img.height;
  ratio = Math.min(hRatio, vRatio);
  var centerShift_x = (ctx.canvas.width - img.width * ratio) / 2;
  var centerShift_y = (ctx.canvas.height - img.height * ratio) / 2;
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  ctx.drawImage(img, 0, 0, img.width, img.height,
    centerShift_x, centerShift_y, img.width * ratio, img.height * ratio);
}
var oldVal = "";

$("#position").on("change keyup paste", function () {
  var currentVal = $(this).val();
  if (currentVal == oldVal) {
    return; //check to prevent multiple simultaneous triggers
  }

  oldVal = currentVal;
  //action to be performed on textarea changed
  updateSelectMenu();
  drawCanvas();
});

function updateSelectMenu() {
  for (a in pointsOptions.options) {
    pointsOptions.options.remove(0);
  }
  points = Object.keys(logic_forms.point_positions)
  for (var key in points) {
    if (points[key] == "") {
      continue;
    }
    var opt = document.createElement('option');
    opt.value = points[key];
    opt.innerHTML = points[key];
    pointsOptions.appendChild(opt);
  }
}

updateSelectMenu();

var textOffset = [10, 5];

function drawCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawImageScaled(ctx, image);

  ctx.font = "20px Arial";
  for (var point in logic_forms.point_positions) {
    var letterX = logic_forms.point_positions[point][0];
    var letterY = logic_forms.point_positions[point][1];
    ctx.fillText(point, letterX - textOffset[0], letterY - textOffset[1]);
  }
}

