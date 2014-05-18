$(document).ready(function(){
    $(".word, .bingofield").bind("mouseover", function(){
        $("#titletext").text($(this).attr("title"));
    }).bind("mouseout", function(){
        $("#titletext").html("&nbsp;");
    })
})
