var ShareSelector = (function() {

  var init = function() {

    if($('#share-dropdown').length == 0)
      return;

    $('[data-placement="tooltip"],[data-toggle="tooltip"]').tooltip()

    var iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

    if(iOS) {
      $('.action-copy button').remove();
      $('.paste .button-container input').css('padding', '10px');
    }
    else  
      $('.action-copy button').on("click", function(e) {

        var element = $(this).parent().parent().find('.btn-group input')[0];

        element.setSelectionRange(0, element.value.length);

        $(this).tooltip('hide');

        try {
          document.execCommand('copy');
        } catch(err) { }

        $(element).tooltip('show');

        setTimeout(function() {

          $(element).tooltip('hide');

        }, 1000);

        e.stopPropagation();
      });

    $('#share-dropdown input').on("click", function(e) {

      this.setSelectionRange(0, this.value.length);
    });
  }

  return {
    'initialize': init
  }
})();

$(document).ready(function() {

  ShareSelector.initialize();
});