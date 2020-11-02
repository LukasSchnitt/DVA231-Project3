"use strict";
$(function(){
    $("#delete-cocktail").click(function (){
        var id = $("#selected-drink-id").attr("value");
        var is_personal_cocktail = $("#selected-drink-from-local-db").attr("value");
        $.ajax("/cocktail",{
            method: 'DELETE',
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            data:{
            "cocktail_id": id,
            "is_personal_cocktail": is_personal_cocktail
            },
            statusCode: {
                200: function(){
                    alert("Cocktail Banned or Unbanned");
                    if($(location).attr("pathname") == "/"){
                        location.reload();
                    }
                },
                400: function(){
                    location.reload();
                }
            }
        });
    });
});