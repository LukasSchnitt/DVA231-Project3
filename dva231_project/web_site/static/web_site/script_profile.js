
$(document).ready(function(){
    $.ajax('/bookmark', 
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

});


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

