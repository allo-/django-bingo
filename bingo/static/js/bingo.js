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
        vote_veto_link.click(function(){
            form = $(obj);
            form.find("input[name=vote]").val("-");
            ajax_submit(form);
            var field_id = $(obj).find("input[name='field_id']").val()
            $("[data-field-id=" + field_id + "]").removeClass("active").addClass("veto");
            return false;
        })
        vote_neutral_link.click(function(){
            form = $(obj);
            form.find("input[name=vote]").val("0");
            ajax_submit(form);
            var field_id = $(obj).find("input[name='field_id']").val()
            $("[data-field-id=" + field_id + "]").removeClass("active").removeClass("veto");
            return false;
        })
        vote_up_link.click(function(){
            form = $(obj);
            form.find("input[name=vote]").val("+");
            ajax_submit(form);
            var field_id = $(obj).find("input[name='field_id']").val()
            $("[data-field-id=" + field_id + "]").addClass("active").removeClass("veto");
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
