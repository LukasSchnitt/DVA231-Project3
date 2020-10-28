var bookmarked_ids = [];

$( document ).ready(function() {

    $.ajax('/bookmark', 
    {
        dataType: 'json', 
        data: {'id': $('#user_id').attr('value')},
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
        },
        success: function (data) {
            $.each(data, function(k, val){
                bookmarked_ids.push(val.id);
            })

        }
    });
    $('#login-btn').on('click', function(){
        $('#login-modal').modal('show');  // show the modal
    });

    $('#register-btn').on('click', function(){
        $('#register-modal').modal('show');  // show the modal
    });
    $('#over-18').on('change', function(){
        $('label[for="over-18"]').css('color', '#212529');
    });

    $('#scroll-up').on('click', function(){
        $("html, body").animate({scrollTop: 0}, 1000);
    });

    $('#bookmark-cocktail').on('click', function(){

        var id = $('#selected-drink-id').attr('value');
        var is_personal_cocktail = $('#selected-drink-from-local-db').attr('value');

        toggle_bookmark(id, is_personal_cocktail);
    });

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

    $('#submit-review').on('click', function(){
        var rating = $('#review-rating-submit').rate("getValue");
        var review = $('#add-review-text').val();
        var id = $('#selected-drink-id').attr('value');
        var is_personal_cocktail = $('#selected-drink-from-local-db').attr('value');


        $.ajax('/review', 
        {
            method: 'POST',
            dataType: 'json',
            // TODO
            data: {'rating': rating, 'comment': review, 'cocktail_id': id, 'is_personal_cocktail': is_personal_cocktail},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            statusCode: {
                200: function() {

                }
              }
        });
        
    })

    $('#register-submit-btn').on('click', function(){
        if (validate_inputs($(this).parent()) && validate_registration()){
            $('#missing-inputs-registration-label').hide();
            register_user();
        }
    });

    $('#login-submit-btn').on('click', function(){

        if (!validate_inputs($(this).parent())){
            $('#missing-inputs-login').show();
        } else{
            $('#missing-inputs-login').hide();
            login_user();
        }
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

    $('#random-drink-btn').on('click', function(){

        $('#selected-drink-rating').remove();
        $('#selected-drink-ranking-container').append(
            '<div class="rating" id="selected-drink-rating"></div>'
        );

        $('#cocktail-modalingredients').empty();
        $('#drink-amounts').empty();
        $.ajax('/cocktail', 
        {
            dataType: 'json', // type of response data
            data: {'random': 1},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            success: function (data) {
                
                var from_db = JSON.parse(data).source === "DB" ? 1 : 0;

                data = JSON.parse(data).random_cocktail;
                $('#cocktail-modal-img').attr('src', data.picture);  // set the image
                $('#cocktail-modal-name').text(data.name)  // set the title

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
    
                // activate_ranking();

                $('#selected-drink-id').attr('value', data.id);
                $('#selected-drink-from-local-db').attr('value', from_db);

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
                $('#cocktail-modal').modal('show');  // show the modal
            }
        });
    });

    $('#search-drink-btn').on('click', function(){
        // get the cokctails from the ingredients
        var ingredients = $('#ingredients-search').val();
        $.ajax('/cocktail', 
        {
            dataType: 'json', // type of response data
            data: {'ingredients': ingredients},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
            },
            success: function (data) {
                $('#show-more-btn').show();
                fill_drink_container(data);
                activate_cells(ingredients, bookmarked_ids);
            }
        });

        $('#drinks-grid-container').fadeIn(400);
        $([document.documentElement, document.body]).animate({
            scrollTop: $("#drinks-grid-container").offset().top
        }, 1000);
        $('#scroll-up').fadeIn();

    });



});

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
                    $('#bookmark-cocktail').attr('bookmarked', '0');
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
                    $('#bookmark-cocktail').attr('bookmarked', "1");
                    bookmarked_ids.push(parseInt(id));
                }
              }
        });
    }

}

function fill_reviews(data){

    $('#review-rating-submit').rate()

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

    $.each(data, function(i, review_obj){
        $('#reviews-from-db-container').append(
            '<div class="review-container w-100 mb-3">' + 
                '<label class="review-username d-inline">' + review_obj.username + '</label>' + 
                '<div class="review-text-wrapper w-100">' + 
                    '<div class="rating review-rating" id="' + review_obj.id +'"></div>' +
                    '<p>' + review_obj.comment + '</p>' + 
                '</div>' +
        '</div>'
        );
        options.initial_value = review_obj.rating;
        $('#' + review_obj.id).rate(options);
    })

}

function validate_inputs(modal_obj){
    var i = 0;

    $.each(modal_obj.find('input').not('#over-18'), function() {
        if (!$(this).val()){
            $(this).css('border-color', 'red');
            $('#missing-inputs-registration-label').show();
        } else{
            $(this).css('border-color', '#ced4da');
            i++;
        }
    });
    return (i === modal_obj.find('input').not('#over-18').length);
}

function validate_registration(){

    if (!$('#over-18').is(':checked')){
        $('label[for="over-18"]').css('color', 'red');
        return false;
    }

    var password = $('#register-password').val();
    var retyped_password = $('#register-password-retyped').val();

    if (password !== retyped_password){
        $('#invalid-password-retype').show();
        return false;
    } else{
        $('#invalid-password-retype').hide();
        return true; 
    }
}

function register_user(){
    var username = $('#register-username').val();
    var password = $('#register-password').val();

    $.ajax('/user', 
    {
        dataType: 'json',
        method: 'PUT',
        data: {'username': username, 'password': password},
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
        },
        statusCode: {
            201: function() {
              $('#registration-success').show();
            },
            226: function(){
                $('#username-taken').show();
            },
            400: function(){
                $('#egister-404').show(); 
            }
          }
    });
}

function login_user(){
    var username = $('#login-username').val();
    var password = $('#login-password').val();


    $.ajax('/user', 
    {
        dataType: 'json',
        method: 'POST',
        data: {'username': username, 'password': password},
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
        },
        statusCode: {
            200: function() {
                location.reload();
            },
            403: function(){
                $('#login-403').show();
            },
            404: function(){
                $('#login-404').show();
            }
          }
    });
}

function activate_ranking(){
    var options = {
        max_value: 5,
        step_size: 0.5,
        initial_value: 0,
        selected_symbol_type: 'utf8_star', // Must be a key from symbols
        cursor: 'normal',
        readonly: false,
        change_once: true, // Determines if the rating can only be set once
    }
    
        $("#selected-drink-rating").rate(options);
        $('.rating').rate(options);
}

function fill_drink_container(data){
    $('#drinks-grid-container').empty();

    data = JSON.parse(data);

    var data_api = data.cocktails_API;
    var data_db = data.cocktails_DB;

    if ($.isEmptyObject(data_api) && $.isEmptyObject(data_db)){
        $('#no-drinks-info').fadeIn(200);
        $('#show-more-btn').hide();
    } else{
        $('#no-drinks-info').hide();
        $('#show-more-btn').fadeIn(200);
    }

    $.each(data_api, function(i, val) {
        if (i%3 == 0){ $('#drinks-grid-container').append('<div class="row d-inline-flex mb-4 drinks-row-holder"></div>');}
        $('.drinks-row-holder').last().append(
           '<div class="col-lg mt-2">' + 
                '<div class="cocktail-cell shadow" id="' + val.id +'" from-db=0>' + 
                    '<img src="' + val.picture + '">' +
                    '<div class="cocktail-cell-description">' +
                        '<p class="name">' + val.name + '</p>' +
                        // '<div class="rating align-middle" data-rate-value=5></div>' +
                    '</div> ' +              
                '</div>' +
            '</div>'
        );
    });

    $.each(data_db, function(i, val) {
        if (i%3 == 0){ $('#drinks-grid-container').append('<div class="row d-inline-flex mb-4 drinks-row-holder"></div>');}
        $('.drinks-row-holder').last().append(
           '<div class="col-lg mt-2">' + 
                '<div class="cocktail-cell shadow" id="' + val.id +'" from-db=1>' + 
                    '<img src="' + val.picture + '">' +
                    '<div class="cocktail-cell-description">' +
                        '<p class="name">' + val.name + '</p>' +
                        // '<div class="rating align-middle" data-rate-value=5></div>' +
                    '</div> ' +              
                '</div>' +
            '</div>'
        );
    });

}

function activate_cells(ingredients, bookmarked_ids){

    $('.cocktail-cell').on('click', function(){
        $('#cocktail-modalingredients').empty();
        $('#drink-amounts').empty();
        $('#reviews-container').hide();
        $('#show-reviews-btn').html('Show reviews<i class="fas fa-chevron-down ml-2">');
        // this handles clicking on cocktail to get more information
        var id = $(this).attr('id');
        var bookmarked = bookmarked_ids.includes(parseInt(id));

        $('#selected-drink-id').attr('value', id);
        $('#selected-drink-from-local-db').attr('value', $(this).attr('from-db'));


        $('#cocktail-modal-img').attr('src', $(this).find('img').attr('src'));  // set the image
        $('#cocktail-modal-name').text($(this).find('.name').text())  // set the title

        get_cocktail_details(id.substring(), ingredients, bookmarked);
        $('#cocktail-modal').modal('show');  // show the modal
    })
}

function get_cocktail_details(id, query_ingredients, bookmarked){

    $('#bookmark-cocktail').html('<i class="far fa-bookmark"></i>');
    $('#bookmark-cocktail').attr('bookmarked', "0")

    $('#selected-drink-rating').remove();
    $('#selected-drink-ranking-container').append(
        '<div class="rating" id="selected-drink-rating"></div>'
    );

    if (bookmarked){
        $('#bookmark-cocktail').html('<i class="fas fa-bookmark"></i>');
        $('#bookmark-cocktail').attr('bookmarked', "1")
    }

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
                if (query_ingredients.toLowerCase().includes(k.toLowerCase())){
                    $('#cocktail-modalingredients').append(
                        "<p class='ingredient ingredient-searched'>" + k + "</p>"
                    );
                } else{
                    $('#cocktail-modalingredients').append(
                        "<p class='ingredient'>" + k + "</p>"
                    );
                }

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