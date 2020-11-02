"use strict";
var selected_id=-1;
function selected(id, username){
    $("#ban-users-list").hide();
    $("#ban-username-input").val(username);
    selected_id=id;
}
var user_list="";
$.ajax(
    "/user",{
        method: 'GET',
        dataType: 'json',
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
        },
        statusCode: {
            404: function(){
                window.reload();
            }
        },
        success: function(data){
            user_list=data;
        }
});
$(function(){
    $("#ban-user-btn").click(function(){
        $("#ban-user-modal").modal("toggle");
    });
    $("#ban-username-input").keyup(function(){
        var val=this.value
        $("#ban-users-list").empty();
        if(val==""){
            return;
        }
        $.each(user_list,function(unused, row){
            if(row['username'].includes(val)){
                let elem="<p onclick=\"selected('"+row['id']+"','"+row['username']+"')\" >"+row['username']+"</p>";
                $("#ban-users-list").append(elem);
            }
        });
    });
    $("#ban-confirm-btn").click(function(){
        $("#ban-username-input").val("");
        $("#ban-confirm-btn").attr("disabled",true);
        $.ajax("/user",{
            method: 'DELETE',
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            data:{"id": selected_id},
            statusCode: {
                200: function(){
                    alert("user banned successfully");
                    $("#ban-confirm-btn").attr("disabled",false);
                    $("#ban-users-list").show();
                },
                401: function(){
                    location.reload();
                }
            }
        });
    });
});