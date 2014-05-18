$(document).ready(function(){
    $("li.word, td.bingofield").bind("mouseover", function(){
        $("#titletext").text($(this).attr("title"));
        $(this).attr("title", "");
    }).bind("mouseout", function(){
        $(this).attr("title", $("#titletext").text());
        $("#titletext").html("&nbsp;");
    })
})
