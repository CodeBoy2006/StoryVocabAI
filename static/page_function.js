$(document).ready(function () {
    $(".word_card").click(function () {
        $("#info-" + $(this).attr("id")).slideToggle();
        console.log($(this).attr("id"));
    });

    $(".speak").click(function () {
        console.log($(this).attr("word"));
        var pronunciation = new Audio("http://dict.youdao.com/dictvoice?audio=" + $(this).attr("word"));
        pronunciation.play();
    });

    $(".delete").click(function () {
        console.log($(this).attr("id-word"));
        const idword = $(this).attr("id-word");
        $.ajax({
            type: "post",
            url: "delete_word",
            async: true,
            data: JSON.stringify({
                target: parseInt(idword),
                now: new Date().getTime()
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            complete: function (data) {
                console.log(idword + "Deleted Successfully");
                $(`div[id-word='${idword}']`).remove();
            }
        });
    });

    $(".export").click(function () {
        $(".cssload-loader").show(1000, "linear");
        $.ajax({
            type: "post",
            url: "export",
            async: true,
            data: JSON.stringify({
                type: "CSV",
                now: new Date().getTime()
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            complete: function (data) {
                console.log("Exported to CSV Successfully");
                console.log(data.responseJSON.file);
                window.location.href = "static/export/" + data.responseJSON.file;
                $(".cssload-loader").hide(1000, "linear");
            }
        });
    });

    $(".manual_btn").click(function () {
        $(".cssload-loader").show(1000, "linear");
        $.ajax({
            type: "post",
            url: "add_single_word",
            async: true,
            data: JSON.stringify({
                word: $("#input").val(),
                now: new Date().getTime()
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            complete: function (data) {
                console.log("Added Successfully");
                $(".cssload-loader").hide(1000, "linear");
                location.reload();
            }
        });
    });

    $(".story").click(function () {
        $.ajax({
            type: "post",
            url: "story",
            async: true,
            data: JSON.stringify({
                now: new Date().getTime()
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            beforeSend: function () {
                $(".cssload-loader").show(1000, "linear");
            },
            complete: function (data) {
                console.log("Wrote Successfully");
                $(".cssload-loader").hide(1000, "linear");
                $("#storycontent").html(data.responseJSON.story)

                for(let x of data.responseJSON.words) {
                    $(".word_detail").append($(`.group[id-word='${x.id}']`).html())
                }

                $(".dialog").show(500);

                $(".word_detail").find(".panel").slideToggle();

            }
        });
    });

    $(".close_dialog_btn").click(function () {
        $(".dialog").hide(500)
    });
});
