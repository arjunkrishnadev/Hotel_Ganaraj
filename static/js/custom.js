// to get current year
function getYear() {
    var currentDate = new Date();
    var currentYear = currentDate.getFullYear();
    document.querySelector("#displayYear").innerHTML = currentYear;
}

getYear();


// isotope js
$(window).on('load', function () {
    $('.filters_menu li').click(function () {
        $('.filters_menu li').removeClass('active');
        $(this).addClass('active');

        var data = $(this).attr('data-filter');
        $grid.isotope({
            filter: data
        })
    });

    var $grid = $(".grid").isotope({
        itemSelector: ".all",
        percentPosition: false,
        masonry: {
            columnWidth: ".all"
        }
    })
});

// nice select
$(document).ready(function() {
    $('select').niceSelect();
  });

/** google_map js **/
function myMap() {
    var mapProp = {
        center: new google.maps.LatLng(40.712775, -74.005973),
        zoom: 18,
    };
    var map = new google.maps.Map(document.getElementById("googleMap"), mapProp);
}

// client section owl carousel
$(".client_owl-carousel").owlCarousel({
    loop: true,
    margin: 0,
    dots: false,
    nav: true,
    navText: [],
    autoplay: true,
    autoplayHoverPause: true,
    navText: [
        '<i class="fa fa-angle-left" aria-hidden="true"></i>',
        '<i class="fa fa-angle-right" aria-hidden="true"></i>'
    ],
    responsive: {
        0: {
            items: 1
        },
        768: {
            items: 2
        },
        1000: {
            items: 2
        }
    }
});

// Background Image Slider - Sync with Carousel (text stays visible)
$(document).ready(function() {
    // Function to update background image based on active carousel slide
    function updateBackgroundImage() {
        var activeSlide = $('.carousel-item.active').index();
        $('.bg-box .bg-slide').removeClass('active');
        $('.bg-box .bg-slide[data-slide="' + activeSlide + '"]').addClass('active');
    }

    // Update on carousel slide start event to sync with text transition (0.6s)
    $('#customCarousel1').on('slide.bs.carousel', function(e) {
        var nextSlide = $(e.relatedTarget).index();
        $('.bg-box .bg-slide').removeClass('active');
        $('.bg-box .bg-slide[data-slide="' + nextSlide + '"]').addClass('active');
    });

    // Fallback: Update on carousel slide complete event
    $('#customCarousel1').on('slid.bs.carousel', function() {
        updateBackgroundImage();
    });

    // Also update when carousel indicators are clicked
    $('.carousel-indicators li').on('click', function() {
        var slideIndex = $(this).data('slide-to');
        $('.bg-box .bg-slide').removeClass('active');
        $('.bg-box .bg-slide[data-slide="' + slideIndex + '"]').addClass('active');
    });

    // Initialize on page load
    updateBackgroundImage();
});