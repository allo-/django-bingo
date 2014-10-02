$(document).ready(function(){
    // dummy, for when no ajax request was executed, yet
    var ajaxRequest = {"abort": function(){}};
    var interval = null;

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
        var veto_link = $("<a>").attr("href", "#").attr("title", "veto").addClass("veto").text("[-]");

        function vote(form, what){
            form.find("input[name=vote]").val(what);
            ajax_submit(form, ajax_vote_url + bingo_board + "/", update_numbers);
            var field_id = $(obj).find("input[name='field_id']").val();
            var fields = $("[data-field-id=" + field_id + "]");
            mark_field(fields, what);
        }

        veto_link.click(function(){
            if($(obj).parent().hasClass("veto")){
                vote($(obj), "0");
            } else {
                vote($(obj), "-");
            }
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
    if(document.getElementById("rate_form")){
        $("#rate_form").hide();
        $("span.rating, span.clearrating").click(function(){
            var form = $("#rate_form");
            var rating = $(this).attr("data-rating")
            $("span.rating").each(function(){
                if(rating != "None" && $(this).attr("data-rating") <= rating){
                    $(this).attr("data-active", "true");
                }else{
                    $(this).attr("data-active", "false");
                }
            })
            $(form).find("option[value="+rating+"]").attr("selected", true);
            ajax_submit(form, form.attr("action"), null);
        }).addClass("clickable");
        $("span.rating").mouseover(function(){
            var rating = $(this).attr("data-rating");
            $("span.rating").each(function(){
                if($(this).attr("data-rating") <= rating){
                    $(this).html("&#9733");
                }else{
                    $(this).html("&#9734");
                }
            })
        });
        // hover
        $("span.clearrating").mouseover(function(){
            $(this).html("&#10008");
            $("span.rating").each(function(){
                $(this).html("&#9734");
            });
        }).mouseout(function(){
            $(this).html("&#10007");
        // unset display: none (hidden for users without JS), mark as clickable
        }).css("display", "").addClass("clickable");

        $("span.ratings").bind("mouseout click", function(){
            $("span.rating").each(function(){
                if($(this).attr("data-active") == "true"){
                    $(this).html("&#9733");
                }else{
                    $(this).html("&#9734");
                }
            })
        })
    }

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

    if(polling_interval == 0){
        // sane default
        polling_interval = 10;
    }

    // enabled and the browser supports server-sent events
    if(use_sse && !!EventSource) {
        var source = new EventSource(sse_url);

        // votes
        source.addEventListener("word_votes", function(e){
            var data = JSON.parse(e.data);
            var objs = $("[data-word-id="+data['word_id']+"]");
            var vote_count = data['vote_count'];
            $(objs).find("span.votes").text(vote_count);
        }, false);

        source.addEventListener("field_vote", function(e){
            var data = JSON.parse(e.data);
            var objs = $("[data-field-id="+data['field_id']+"]");
            var vote = data['vote'];
            mark_field(objs, vote);
        }, false);

        // number of users (boards)
        source.addEventListener("num_users", function(e){
            var data = JSON.parse(e.data);
            $('#num_users').text(data['num_users'])
        }, false);

        source.addEventListener("num_active_users", function(e){
            var data = JSON.parse(e.data);
            $('#num_active_users').text(data['num_active_users'])
        }, false);

        source.addEventListener("open", function(e){
            if(interval){
                clearInterval(interval)
            }
            // 0 disables polling
            if(polling_interval_sse != 0){
                interval = setInterval(update_numbers, polling_interval_sse * 1000);
            }
        });
        source.addEventListener("error", function(e){
            if(interval){
                clearInterval(interval)
            }
            // use normal polling without server-sent
            interval = setInterval(update_numbers, polling_interval * 1000);
        });
    } else {
        interval = setInterval(update_numbers, polling_interval * 1000);
    }
})
