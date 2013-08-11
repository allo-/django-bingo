$(document).ready(function(){
    $("form.voteform").each(function(idx, obj){
        $(obj).find("input[type=submit]").remove();
        var vote_field = $("<input>").attr("name", "vote").attr("type", "hidden");
        var vote_veto_link = $("<a>").attr("href", "#").addClass("vote_link").text("[-]");
        var vote_neutral_link = $("<a>").attr("href", "#").addClass("vote_link").text("[0]");
        var vote_up_link = $("<a>").attr("href", "#").addClass("vote_link").text("[+]");

        function ajax_submit(form){
            var data = {"ajax": true};
            form.find("input").each(function(idx, obj){
                form_field = $(obj);
                data[form_field.attr("name")] = form_field.val();
            })
            $.ajax(form.attr("action"), {"type": "post", "data": data});
        }

        function vote(form, what){
            form.find("input[name=vote]").val(what);
            ajax_submit(form);
            var field_id = $(obj).find("input[name='field_id']").val();
            var fields = $("[data-field-id=" + field_id + "]");
            if(what == "+") {
                fields.addClass("active").removeClass("veto");
            } else if(what == "0") {
                fields.removeClass("active").removeClass("veto");
            } else if(what == "-") {
                fields.removeClass("active").addClass("veto");
            }
        }

        vote_veto_link.click(function(){
            vote($(obj), "-");
            return false;
        });
        vote_neutral_link.click(function(){
            vote($(obj), "0");
            return false;
        });
        $(vote_up_link).click(function(){
            vote($(obj), "+");
            return false;
        });
        $(obj).parent().click(function(){
            // toggle
            if($(obj).parent().hasClass("active")){
                vote($(obj), "0");
            } else {
                vote($(obj), "+");
            }
            return false;
        });

        $(obj).append(vote_field);
        $(obj).append(vote_veto_link);
        $(obj).append(" ");
        $(obj).append(vote_neutral_link);
        $(obj).append(" ");
        $(obj).append(vote_up_link);
    })
})
