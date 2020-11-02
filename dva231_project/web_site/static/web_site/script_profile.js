
$(document).ready(function(){
    fill('/bookmark', $('#drinks-grid-container-bookmarked'));
    fill('/cocktail', $('#drinks-grid-container-own'));

    $('.logo').on('click', function(){
        document.location.href="/";
    });

    document.querySelector('.custom-file-input').addEventListener('change',function(e){
        var fileName = document.getElementById("cocktail-img").files[0].name;
        var nextSibling = e.target.nextElementSibling
        nextSibling.innerText = fileName
      })

    $('#add-cocktail-btn').on('click', function(){
        $('#add-cocktail-modal').modal('show');
        $('#ingredient-input-wrapper').children().not(':first').remove();
    });

    $('#add-ingredient-field').on('click', function(){
        $('#ingredient-input-wrapper').append(
            $('#ingredient-row-template').clone().attr('id', '').show().html()
        )
    });

    $('#bookmarked-cocktails-btn').on('click', function(){
        remove_active();
        $(this).parent().addClass('active');
        $('#drinks-grid-container-own').slideUp(400)
        $('#drinks-grid-container-bookmarked').slideDown(400)
    })

    $('#my-cocktails-btn').on('click', function(){
        $('#drinks-grid-container-bookmarked').slideUp(400)
        remove_active();
        $(this).parent().addClass('active');
        $('#drinks-grid-container-own').slideDown(400)

    });

    $('#logout-btn').on('click', function(){
        $.ajax('/user', 
        {
            method: 'HEAD',
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            statusCode: {
                200: function() {
                  location.reload()
                }
              }
        });
    });

    var img_bytes = "";

    $('#cocktail-img').change(function() {
        var reader = new FileReader();
        reader.onload = function() {
            img_bytes=reader.result;
        }
        reader.readAsDataURL(this.files[0]);
      
      });

    $('#delete-personal-cocktail-btn').on('click', function(){
        var id = $('#selected-drink-id').attr('value');

        $.ajax('/cocktail', 
        {
            method: 'DELETE',
            dataType: 'json',
            data: {'id': id},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            }, 
            statusCode: {
                200: function() {
                  $('#' + id).hide();
                  $('#cocktail-modal').modal("hide");
                }
              }
        });
    });

    $('#submit-cocktail-btn').on('click', function(){

        if (!check_new_cocktail_input()){
            return;
        }
        
        var name = $('#new-cocktail-name').val();
        var recipe = $('#new-cocktail-recipe').val();
        var img = img_bytes;
        var extension = $('label[for=cocktail-img]').text().split('.').pop();
        var description = "NO DESCRIPTION"; // empty by default, might be implemented in the future

        var ingredients = {};
        $('#ingredients-container').find('.ingredient-row').each(function(){
            ingredients[$(this).find('.ingredient-name').val()] = $(this).find('.ingredient-amount').val();
        });

        $.ajax('/cocktail', 
        {
            method: 'POST',
            dataType: 'json',
            data: {'name': name, 
                   'recipe': recipe, 
                   'img': img,
                   'extension': extension,
                   'description': description,
                   'ingredients': JSON.stringify(ingredients)
                   },
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            }, 
            statusCode: {
                201: function() {
                  location.reload();
                },
                400: function(){
                    alert("Invalid Data");
                }
              }
        });


    });


    $('#submit-review').on('click', function(){
        var rating = $('#review-rating-submit').rate("getValue");
        var review = $('#add-review-text').val();
        var id = $('#selected-drink-id').attr('value');
        var is_personal_cocktail = $('#selected-drink-from-local-db').attr('value');


        $.ajax('/review', 
        {
            method: 'POST',
            dataType: 'json',
            data: {'rating': rating, 'comment': review, 'cocktail_id': id, 'is_personal_cocktail': is_personal_cocktail},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            statusCode: {
                201: function() {
                    $('#new-review-container').slideUp(200);
                    $.ajax('/review', 
                    {
                        method: 'GET',
                        dataType: 'json',
                        data: {'cocktail_id': id, 'is_personal_cocktail': is_personal_cocktail},
                        beforeSend: function (xhr, settings) {
                            xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
                        },
                        statusCode: {
                            200: function(data) {
                                fill_reviews(data);
                                $('#selected-drink-rating').remove();
                                $('#selected-drink-ranking-container').append(
                                    '<div class="rating" id="selected-drink-rating"></div>'
                                );
                                var review_rating = 0;

                                $('#reviews-from-db-container').find('.review-rating').each(function(){
                                    review_rating += $(this).rate("getValue");
                                });
                                var review_no = $('#reviews-from-db-container').find('.review-rating').length;
                                $('#selected-drink-rating').rate();
                                $('#selected-drink-rating').rate("setValue", review_rating/review_no);
                            }
                          }
                    });
                }
              }
        });
        
    })

    
    $('#show-reviews-btn').on('click', function(){
        $('#reviews-container').slideToggle(400);

        $(this).text()==='Show reviews' ? 
            $(this).html('Hide reviews<i class="fas fa-chevron-up ml-2">') : 
            $(this).html('Show reviews<i class="fas fa-chevron-down ml-2">');
       
    
        var id = $('#selected-drink-id').attr('value');
        var is_personal_cocktail = $('#selected-drink-from-local-db').attr('value');

        $.ajax('/review', 
        {
            method: 'GET',
            dataType: 'json',
            data: {'cocktail_id': id, 'is_personal_cocktail': is_personal_cocktail},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            statusCode: {
                200: function(data) {
                    fill_reviews(data);
                }
              }
        });

    });


    $('#edit-review').on('click', function(){
        var rating = $('#review-rating-submit').rate("getValue");
        var review = $('#add-review-text').val();
        var id = $('#selected-drink-id').attr('value');
        var is_personal_cocktail = $('#selected-drink-from-local-db').attr('value');

        // review_obj.user_id == $('#user_id').attr('value')
        var review_id = $('.review-id').filter(function(){
            return $(this).parent().find('.review-user-id').attr('value') == $('#user_id').attr('value')
        }).attr('value')

        $.ajax('/review', 
        {
            method: 'PATCH',
            dataType: 'json',
            data: {'id': review_id, 
                   'rating': rating, 
                   'comment': review, 
                   'cocktail_id': id, 
                   'is_personal_cocktail': is_personal_cocktail},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            statusCode: {
                200: function() {
                    $('#new-review-container').slideUp(200);
                    $.ajax('/review', 
                    {
                        method: 'GET',
                        dataType: 'json',
                        data: {'cocktail_id': id, 'is_personal_cocktail': is_personal_cocktail},
                        beforeSend: function (xhr, settings) {
                            xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
                        },
                        statusCode: {
                            200: function(data) {
                                fill_reviews(data);
                                $('#selected-drink-rating').remove();
                                $('#selected-drink-ranking-container').append(
                                    '<div class="rating" id="selected-drink-rating"></div>'
                                );
                                var review_rating = 0;

                                $('#reviews-from-db-container').find('.review-rating').each(function(){
                                    review_rating += $(this).rate("getValue");
                                });
                                var review_no = $('#reviews-from-db-container').find('.review-rating').length;
                                $('#selected-drink-rating').rate();
                                $('#selected-drink-rating').rate("setValue", review_rating/review_no);

                            }
                          }
                    });
                }
              }
        });
        
    })

});

function check_new_cocktail_input(){

    var valid = true;
    $('#add-cocktail-modal :input:visible').not('button').each(function(){
        if (!$(this).val()){
            $(this).css('border-color', 'red');
            valid = false;
        } else{
            $(this).css('border-color', '#ced4da');
        }
    });
    return valid;
}

function remove_active(){
    $('.nav-item').each(function(){
        $(this).removeClass('active');
    });
}

function fill(url, container){
    $.ajax(url, 
    {
        dataType: 'json', 
        data: {'id': $('#user_id').attr('value')},
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
        },
        success: function (data) {
            fill_drink_container(data, container);
            activate_cells();
        }
    });


    $('#bookmark-cocktail').on('click', function(){

        var id = $('#selected-drink-id').attr('value');
        var is_personal_cocktail = $('#selected-drink-from-local-db').attr('value');

        toggle_bookmark(id, is_personal_cocktail);
    });



}

function fill_drink_container(data, container){
    // data = JSON.parse(data);

    if (data.hasOwnProperty("user_cocktails")){
        data = data.user_cocktails;
    }


    $.each(data, function(i, val) {
        if (i%2 == 0){ container.append('<div class="row d-inline-flex mb-4 drinks-row-holder"></div>');}
        container.find('.drinks-row-holder').last().append(
           '<div class="col-lg mt-2">' + 
                '<div class="cocktail-cell shadow" id="' + val.id +'" from-db="' + val.is_personal_cocktail + '">' +
                    '<img src="' + val.picture + '">' +
                    '<div class="cocktail-cell-description">' +
                        '<p class="name">' + val.name + '</p>' +
                    '</div> ' +              
                '</div>' +
            '</div>'
        );
    });
}


function activate_cells(){
    $('.cocktail-cell').on('click', function(){
        $('#cocktail-modalingredients').empty();
        $('#drink-amounts').empty();
        $('#reviews-container').hide();
        $('#show-reviews-btn').html('Show reviews<i class="fas fa-chevron-down ml-2">');
        // this handles clicking on cocktail to get more information
        var id = $(this).attr('id');

        $('#selected-drink-id').attr('value', id);
        $('#selected-drink-from-local-db').attr('value', $(this).attr('from-db'));


        $('#cocktail-modal-img').attr('src', $(this).find('img').attr('src'));  // set the image
        $('#cocktail-modal-name').text($(this).find('.name').text())  // set the title
        get_cocktail_details(id.substring());
        $('#cocktail-modal').modal('show');  // show the modal
    })
}


function get_cocktail_details(id){

    $('#selected-drink-rating').remove();
    $('#selected-drink-ranking-container').append(
        '<div class="rating" id="selected-drink-rating"></div>'
    );

    $.ajax('/cocktail', 
    {
        dataType: 'json', 
        data: {'id': id, 'is_personal_cocktail': $('#' + id).attr('from-db')},
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
        },
        success: function (data) {
            data = JSON.parse(data);

            $.each(data.ingredients, function(k, val){
                $('#cocktail-modalingredients').append(
                    "<p class='ingredient'>" + k + "</p>"
                );
                
                if (val == null){
                    $('#drink-amounts').append(
                        "<li class='amount'>" + k + "</li>"
                    );
                } else{
                    $('#drink-amounts').append(
                        "<li class='amount'>" + k + ": " + val + "</li>"
                    );
                }
            });
            
            $('#drink-recipe').text(data.recipe);

            var rating;
            if (data.rating == null){
                rating = 0;
            } else{
                rating = data.rating;
            }

            var options = {
                max_value: 5,
                step_size: 0.5,
                initial_value: rating,
                selected_symbol_type: 'utf8_star', // Must be a key from symbols
                cursor: 'normal',
                readonly: true,
            }
            
            $("#selected-drink-rating").rate(options);

        }
    });
}

function fill_reviews(data){

    $('#review-rating-submit').rate()
    $('#submit-review').show();
    $('#edit-review').hide();

    $('#add-review-text').val('')

    var options = {
        max_value: 5,
        step_size: 0.5,
        initial_value: 0,
        selected_symbol_type: 'utf8_star', // Must be a key from symbols
        cursor: 'normal',
        readonly: true,
        change_once: true, // Determines if the rating can only be set once
    }

    $('#reviews-from-db-container').empty();

    $('#new-review-container').show();
    $.each(data, function(i, review_obj){
        var edit_button = '';
        if (review_obj.user_id == $('#user_id').attr('value')){
            $('#new-review-container').hide();
            edit_button = "<button id='edit-review-btn' class='btn'>Edit review</button>" + 
                          "<button id='delete-review-btn' class='btn'>Delete review</button>"
        }

        $('#reviews-from-db-container').append(
            '<div class="review-container w-100 mb-3">' + 
                '<meta class="review-id" value=' + review_obj.id + ">" +
                '<meta class="review-user-id" value=' + review_obj.user_id + ">" +
                '<label class="review-username d-inline">' + review_obj.username + '</label>' + 
                edit_button + 
                '<div class="review-text-wrapper w-100">' + 
                    '<div class="rating review-rating" id="' + review_obj.id +'"></div>' +
                    '<p>' + review_obj.comment + '</p>' + 
                '</div>' +
        '</div>'
        );
        options.initial_value = review_obj.rating;
        $('#' + review_obj.id).rate(options);
    })

    $('#edit-review-btn').on('click', function(){
        $('#add-review-text').val($(this).parent().find('p').text())
        $('#submit-review').hide();
        $('#edit-review').show();
        $('#new-review-container').show();
    })

    $('#delete-review-btn').on('click', function(){

        var review_id = $('.review-id').filter(function(){
            return $(this).parent().find('.review-user-id').attr('value') == $('#user_id').attr('value')
        }).attr('value')

        $.ajax('/review', 
        {
            method: 'DELETE',
            dataType: 'json',
            data: {'id': review_id},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            statusCode: {
                200: function() {
                    $('#selected-drink-rating').remove();
                    $('#selected-drink-ranking-container').append(
                        '<div class="rating" id="selected-drink-rating"></div>'
                    );
                    $('#' + review_id).parent().parent().empty();
                    $('#new-review-container').slideDown(400);
                    var review_rating = 0;

                    $('#reviews-from-db-container').find('.review-rating').each(function(){
                        review_rating += $(this).rate("getValue");
                    });
                    var review_no = $('#reviews-from-db-container').find('.review-rating').length;
                    $('#selected-drink-rating').rate();
                    $('#selected-drink-rating').rate("setValue", review_rating/review_no);
                }
            }
        })
        
    });

}



function toggle_bookmark(id, is_personal_cocktail){

    var bookmarked = $('#bookmark-cocktail').attr('bookmarked') === "1";
    
    if(bookmarked){
        $.ajax('/bookmark', 
        {
            method: 'DELETE',
            dataType: 'json',
            data: {'cocktail_id': id, 'is_personal_cocktail': is_personal_cocktail},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            statusCode: {
                200: function() {
                    $('#bookmark-cocktail').html('<i class="far fa-bookmark"></i>');
                    $('#bookmark-cocktail').attr('bookmarked', 0);                    
                }
              }
        });

    } else{
        $.ajax('/bookmark', 
        {
            method: 'POST',
            dataType: 'json',
            data: {'cocktail_id': id, 'is_personal_cocktail': is_personal_cocktail},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            statusCode: {
                201: function() {
                    $('#bookmark-cocktail').html('<i class="fas fa-bookmark"></i>');
                    $('#bookmark-cocktail').attr('bookmarked', '1')
                }
              }
        });
    }

}