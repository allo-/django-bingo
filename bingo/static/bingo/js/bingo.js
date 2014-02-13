$(document).ready(function(){
    // dummy, for when no ajax request was executed, yet
    var ajaxRequest = {"abort": function(){}};

    function ajax_submit(form, url, success){
        var data = {};
        form.find("input, select").each(function(idx, obj){
            form_field = $(obj);
            data[form_field.attr("name")] = form_field.val();
        })
        ajaxRequest.abort(); // abort any running ajax requests
        ajaxRequest = $.ajax(url, {
            "type": "post",
            "dataType": "json",
            "data": data,
            "success": success 
        });
    }

    $("form.voteform").each(function(idx, obj){
        $(obj).find("input[type=submit]").remove();
        var vote_field = $("<input>").attr("name", "vote").attr("type", "hidden");
        var veto_link = $("<a>").attr("href", "#").addClass("veto").text("[-]");

        function vote(form, what){
            form.find("input[name=vote]").val(what);
            ajax_submit(form, ajax_vote_url + bingo_board + "/", update_numbers);
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

    // ajax for rate form
    $("#rate_form").hide();
    $("span.rating").click(function(){
        var form = $("#rate_form");
        var rating = $(this).attr("data-rating")
        $("span.rating").each(function(){
            if($(this).attr("data-rating") <= rating){
                $(this).attr("data-active", "true");
            }else{
                $(this).attr("data-active", "false");
            }
        })
        $(form).find("option[value="+rating+"]").attr("selected", true);
        ajax_submit(form, form.attr("action"), null);
    });
    $("span.rating").mouseover(function(){
        var rating = $(this).attr("data-rating");
        $("span.rating").each(function(){
            if($(this).attr("data-rating") <= rating){
                $(this).html("&#9733");
            }else{
                $(this).html("&#9734");
            }
        })
    })
    $("span.ratings").mouseout(function(){
        $("span.rating").each(function(){
            if($(this).attr("data-active") == "true"){
                $(this).html("&#9733");
            }else{
                $(this).html("&#9734");
            }
        })
    })

    if(bingo_board == my_board){
        $(".bingofield, .word").not(".middle").each(function(idx, obj){
            $(obj).addClass("clickable");
        });
    }

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
            if(data["is_expired"]){
                window.location.reload()
            }
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
