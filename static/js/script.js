var ShareSelector = (function() {

  var init = function() {

    if($('#copy-code').length == 0)
      return;

    $('[data-placement="tooltip"],[data-toggle="tooltip"]').tooltip()

    // Select text when dropdown shows
    $('.dropdown-parent').on('show.bs.dropdown', function () {

      var element = $(this).find('.btn-group input')[0];

      setTimeout(function() {

        element.focus();
        element.setSelectionRange(0, element.value.length);

      }, 100);

    });

    // Select text when user clicks on the code
    $('#copy-code input').on("click", function(e) {

      this.focus();
      this.setSelectionRange(0, this.value.length);
    });

    // Disable clipboard buttons in Safari
    // until further notice
    var is_chrome = navigator.userAgent.indexOf('Chrome') > -1;
    var is_safari = navigator.userAgent.indexOf("Safari") > -1;
    var is_opera = navigator.userAgent.toLowerCase().indexOf("op") > -1;

    if ((is_chrome)&&(is_safari)) {is_safari=false;}
    if ((is_chrome)&&(is_opera)) {is_chrome=false;}

    if(is_safari) {

      $('.action-copy button').remove();
      return;
    }

    $('.action-copy button').on("click", function(e) {

      var element = $(this).parent().parent().find('.btn-group input')[0];

      element.focus();
      element.setSelectionRange(0, element.value.length);

      $(this).tooltip('hide');

      var copied = false;

      try {

        copied = document.execCommand('copy');

      } catch(err) {}

      if(copied) {

        $(element).tooltip('show');

        setTimeout(function() {

          $(element).tooltip('hide');

        }, 1000);
      }

      e.stopPropagation();
    });
  }

  return {
    'initialize': init
  }
})();

var UserStyleSelector = (function() {

  init = function() {

    if($('.account-form').length == 0)
      return;

    var options = $('.account-form select')[0].options;
    var self = this;

    $('.account-form select').on('keyup', function(event) {

      var selectedIndex = $('.account-form select')[0].selectedIndex;

      if(event.keyCode == 38) { //up

        if(selectedIndex == 0)
          return;

        selectedIndex -= 1;

        var style = this.options[selectedIndex].value;
        $(this).val(style);

        self.changeStyle();

      } else if(event.keyCode == 40) { //down


        if(selectedIndex == options.length - 1)
          return;

        selectedIndex += 1;

        var style = this.options[selectedIndex].value;
        $(this).val(style);

        self.changeStyle();
      }
    });

    $('.account-form select').on('change', function() {

        self.changeStyle();
    });
  }

  changeStyle = function() {

      var element = $('.account-form select')[0];

      var style = element.options[element.selectedIndex].value;

      if(style == '')
        style = DefaultUserStyle;

      var userStyle = UserStyles[style];

      $('.user-style').remove();
      $('<link href="' + userStyle + '" rel="stylesheet" class="user-style"/>').appendTo("head");
  }

  return {
    'initialize': init,
    'changeStyle': changeStyle
  }
})();

var DeleteConfirm = (function() {

  init = function() {

    if($('#delete-paste').length == 0)
      return;

    $('#delete-paste').on('submit', function() {

      return confirm("Are you sure you want to delete this paste?");
    });
  }

  return {
      'initialize': init
  }
})();

$(document).ready(function() {

  autosize($('textarea'));

  DeleteConfirm.initialize();
  UserStyleSelector.initialize();
  ShareSelector.initialize();
});