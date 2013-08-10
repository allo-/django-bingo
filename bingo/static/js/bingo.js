$(document).ready(function(){
    $("form.voteform").each(function(idx, obj){
        $(obj).find("input[type=submit]").remove();
        var vote_field = $("<input>").attr("name", "vote").attr("type", "hidden");
        var vote_veto_link = $("<a>").attr("href", "#").addClass("vote_link").text("[-]");
        var vote_neutral_link = $("<a>").attr("href", "#").addClass("vote_link").text("[0]");
        var vote_up_link = $("<a>").attr("href", "#").addClass("vote_link").text("[+]");

        vote_veto_link.click(function(){
            $(obj).find("input[name=vote]").val("-");
            $(obj).submit();
            return false;
        })
        vote_neutral_link.click(function(){
            $(obj).find("input[name=vote]").val("0");
            $(obj).submit();
            return false;
        })
        vote_up_link.click(function(){
            $(obj).find("input[name=vote]").val("+");
            $(obj).submit();
            return false;
        })

        $(obj).append(vote_field);
        $(obj).append(vote_veto_link);
        $(obj).append(" ");
        $(obj).append(vote_neutral_link);
        $(obj).append(" ");
        $(obj).append(vote_up_link);
    })
})
