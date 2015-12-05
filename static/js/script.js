var LanguageSelector = (function() {

  var init = function() {

    var em = $('#selected-language');

    if(em.length == 0)
      return;

    $('#id_raw_language').on('change', function(element) {

      var value = this.selectedIndex;

      var text = this.options[value].text;

      $(em).html(text);
    });
  }

  return {
    'initialize': init
  }
})();

var ShareSelector = (function() {

  var init = function() {

    if($('#share-dropdown').length == 0)
      return;

    $('[data-placement="tooltip"]').tooltip()

    var label = $('#share-dropdown .dropdown-toggle em');
    var choices = $('#share-dropdown .dropdown-menu a');
    var input = $('#share-dropdown input');

    $(choices).on('click', function() {

      if($(this).hasClass('selected'))
        return;

      $('#share-dropdown a.selected').removeClass('selected');
      $(this).addClass('selected');

      var choice = $(this).data('choice');

      $(label).html($(this).data('legend'));
      $(input).val($(input).data(choice));
    });

    $('#copy-clipboard').on("click", function(e) {

      var element = $('#share-dropdown input')[0];

      element.setSelectionRange(0, element.value.length);

      try {
        document.execCommand('copy');
      } catch(err) { }

      $(input).tooltip('show');

      setTimeout(function() {

        $(input).tooltip('hide');

      }, 1000);
    });

    $(input).on("click", function(e) {

      this.setSelectionRange(0, this.value.length);

      // console.log(this);
      // var range = document.createRange();
      // range.selectNode(this);
      // window.getSelection().addRange(range);

      // try {
      //   document.execCommand('copy');
      // } catch(err) { }

      // $(e.target).one('mouseup', function(e) { e.preventDefault(); });
    });
  }

  return {
    'initialize': init
  }
})();

$(document).ready(function() {

  ShareSelector.initialize();
  LanguageSelector.initialize();
});
