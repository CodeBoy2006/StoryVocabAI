$(document).ready(function() {
  $(".word_card").click(function () {
    $("#info-" + $(this).attr("id")).slideToggle();
    console.log($(this).attr("id"));
  });

  $(".speak").click(function () {
    console.log($(this).attr("word"));
    var pronunciation = new Audio("http://dict.youdao.com/dictvoice?audio="+$(this).attr("word"));
    pronunciation.play();
  });

  $(".delete").click(function () {
    console.log($(this).attr("id-word"));
    var idword = $(this).attr("id-word");
    $.ajax({
        type: "post",
        url: "delete_word",
        async: false, // 使用同步方式
        // 1 需要使用JSON.stringify 否则格式为 a=2&b=3&now=14...
        // 2 需要强制类型转换，否则格式为 {"a":"2","b":"3"}
        data: JSON.stringify({
            target: parseInt(idword),
            now: new Date().getTime() // 注意不要在此行增加逗号
        }),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        complete: function(data) {
            console.log(idword+"Deleted Successfully");
            $(`div[id-word='${idword}']`).remove();
        } // 注意不要在此行增加逗号
    });
  });
});
