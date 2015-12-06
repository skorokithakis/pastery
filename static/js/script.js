var ShareSelector = (function() {

  var init = function() {

    if($('#share-dropdown').length == 0)
      return;

    $('[data-placement="tooltip"],[data-toggle="tooltip"]').tooltip()

    $('.dropdown-parent').on('show.bs.dropdown', function () {

      var element = $(this).find('.btn-group input')[0];

      element.setSelectionRange(0, element.value.length);

    });

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
        style = 'monokai';

      var userStyle = UserStyles[style];

      $('.user-style').remove();
      $('<link href="' + userStyle + '" rel="stylesheet" class="user-style"/>').appendTo("head");
  }

  return {
    'initialize': init,
    'changeStyle': changeStyle
  }
})();

$(document).ready(function() {

  UserStyleSelector.initialize();
  ShareSelector.initialize();
});