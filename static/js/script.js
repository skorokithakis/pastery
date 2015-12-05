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

$(document).ready(function() {

  LanguageSelector.initialize();
});