$( document ).ready(function() {

    $('#search-drink-btn').on('click', function(){
        // TODO: get the stuff from input, send ajax
        // for DEBUG show the hard-coded elements
        $('#drinks-grid-container').fadeIn(400);
        $([document.documentElement, document.body]).animate({
            scrollTop: $("#drinks-grid-container").offset().top
        }, 1000);
    });

    $('.cocktail-cell').on('click', function(){
        // this handles clicking on cocktail to get more information
        $('#cocktail-modal-img').attr('src', $(this).find('img').attr('src'));  // set the image
        $('#cocktail-modal-name').text($(this).find('.name').text())  // set the title
        // set rating
        // set ingredients
        // set recipe
        // set reviews
        $('#cocktail-modal').modal('show');  // show the modal
    })

    // Options for rating
    // https://github.com/auxiliary/rater for reference
    var options = {
    max_value: 5,
    step_size: 0.5,
    initial_value: 0,
    selected_symbol_type: 'utf8_star', // Must be a key from symbols
    cursor: 'normal',
    readonly: true,
    change_once: false, // Determines if the rating can only be set once
    ajax_method: 'POST',
    url: 'http://localhost/test.php',
    additional_data: {} // Additional data to send to the server
}

    $(".rating").rate(options);

});

