
$(document).ready(function(){
    fill('/bookmark');

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
        fill('/cocktail_API');
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

});

function remove_active(){
    $('.nav-item').each(function(){
        $(this).removeClass('active');
    });
}

function fill(url){
    $.ajax(url, 
    {
        dataType: 'json', 
        data: {'id': $('#user_id').attr('value')},
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $('#token').attr('value'));
        },
        success: function (data) {
            fill_drink_container(data);
            activate_cells();
        }
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

}

function fill_drink_container(data){
    $('#drinks-grid-container-bookmarked').empty();

    // data = JSON.parse(data);

    $.each(data, function(i, val) {
        if (i%2 == 0){ $('#drinks-grid-container-bookmarked').append('<div class="row d-inline-flex mb-4 drinks-row-holder"></div>');}
        $('.drinks-row-holder').last().append(
           '<div class="col-lg mt-2">' + 
                '<div class="cocktail-cell shadow" id="' + val.id +'" from-db=0>' + 
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
                '<label class="review-username d-inline">' + 'username' + '</label>' + 
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