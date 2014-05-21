$(document).ready(function(){
    var title_timeout = null;
    $("li.word, td.bingofield").bind("mouseover", function(){
        var field = $(this);
        title_timeout = setTimeout(function(){
            $("#titletext").text(field.attr("title"));
            field.attr("title", "");
            title_timeout = null;
        }, 500);
    }).bind("mouseout", function(){
        if(title_timeout){
            clearTimeout(title_timeout);
        }else{
            $(this).attr("title", $("#titletext").text());
            $("#titletext").html("&nbsp;");
        }
    })
})
