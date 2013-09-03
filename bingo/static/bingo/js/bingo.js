$(document).ready(function(){
    // dummy, for when no ajax request was executed, yet
    var ajaxRequest = {"abort": function(){}};

    $("form.voteform").each(function(idx, obj){
        $(obj).find("input[type=submit]").remove();
        var vote_field = $("<input>").attr("name", "vote").attr("type", "hidden");
        var veto_link = $("<a>").attr("href", "#").addClass("veto_link").text("[-]");

        function ajax_submit(form){
            var data = {};
            form.find("input").each(function(idx, obj){
                form_field = $(obj);
                data[form_field.attr("name")] = form_field.val();
            })
            ajaxRequest.abort(); // abort any running ajax requests
            ajaxRequest = $.ajax(ajax_vote_url + bingo_board + "/", {
                "type": "post",
                "dataType": "json",
                "data": data,
                "success":  update_numbers
            });
        }

        function vote(form, what){
            form.find("input[name=vote]").val(what);
            ajax_submit(form);
            var field_id = $(obj).find("input[name='field_id']").val();
            var fields = $("[data-field-id=" + field_id + "]");
            mark_field(fields, what);
        }

        veto_link.click(function(){
            vote($(obj), "-");
            return false;
        });

        // toggle up / neutral
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
        $(obj).append(veto_link);
    });
    $(".bingofield, .word").not(".middle").each(function(idx, obj){
        $(obj).addClass("clickable");
    });

    function mark_field(obj, vote){
        if(vote == "+") {
            obj.removeClass("veto").addClass("active");
        } else if (vote == "0" ){
            obj.removeClass("veto").removeClass("active");
        } else if (vote == "-" ){
            obj.addClass("veto").removeClass("active");
        }
    }

    function update_numbers(data) {
        if(data != null) {
            $("#num_active_users").text(data["num_active_users"]);
            $("#num_users").text(data["num_users"]);
            $("[data-field-id]").each(function(idx, obj){
                var field_data = data[$(obj).attr("data-field-id")];
                var vote = field_data[0];
                var num_votes = field_data[1]

                mark_field($(obj), vote);
                $(obj).find("span.votes").text(num_votes)
            });
        } else {
            ajaxRequest.abort(); // abort any running ajax requests
            ajaxRequest = $.ajax(ajax_vote_url + bingo_board + "/", {
                "type": "get",
                "dataType": "json",
                "success": update_numbers
            });
        }
    }

    setInterval(update_numbers, 10000)
})
