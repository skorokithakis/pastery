var ShareSelector = (function() {

  var init = function() {

    if($('#copy-code').length == 0)
      return;

    $('[data-placement="tooltip"],[data-toggle="tooltip"]').tooltip({
      'placement': 'top'
    });

    // Select text when dropdown shows
    $('.dropdown-parent').on('show.bs.dropdown', function () {

      var element = $(this).find('.btn-group input')[0];

      setTimeout(function() {

        element.focus();
        element.setSelectionRange(0, element.value.length);

        $(element).tooltip('hide');

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

    if($('.account-form select')[0] == undefined)
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

var ConfirmAction = (function() {

  init = function() {

    if($('[data-confirm]').length == 0)
      return;

    $('[data-confirm]').on('submit', function() {

        var question = $(this).data('confirm');

        return confirm(question);
    });
  }

  return {
      'initialize': init
  }
})();

var LineSelector = (function() {

  lastSelectedLineNumber = '';

  init = function() {

    var self = this;

    $(window).on('hashchange', function() {
      self.parseHash(false);
    });

    if(this.supportsHistory()) {

      $('a[href^="#l-"]').click(function(event) {

        event.preventDefault();

        var url = $(this).attr('href');

        if(TabbedPastes.hasTabs)
            url += '-' + TabbedPastes.activePasteId;

        history.pushState(null, null, url);

        self.parseHash(false);
      });
    }

    this.parseHash(true);
  }

  supportsHistory = function() {
    return !!(window.history && history.pushState);
  }

  parseHash = function(delay) {

    var hash = location.hash;

    if(hash.indexOf('#l-') < 0)
      return;

    if(this.lastSelectedLineNumber != '') {

      $('#line-' + this.lastSelectedLineNumber).removeClass('selected');
      $('a[href=#l-' + this.lastSelectedLineNumber + ']').removeClass('selected');
    }

    var lineObjects= hash.split(/-/);

    if(lineObjects.length > 2)
        TabbedPastes.selectPasteWithId(lineObjects[2]);

    var lineNumber = lineObjects[1];

    var lineElement = $('#line-' + lineNumber);

    $(lineElement).addClass('selected');
    $('a[href=#l-' + lineNumber + ']').addClass('selected');

    this.lastSelectedLineNumber = lineNumber;

    var scrollObject = $(lineElement).offset();
    var scrollHeight = scrollObject.top;
    var windowHeight = $(window).height();

    if(delay) {

      setTimeout(function() {
        window.scrollTo(0, scrollHeight - (windowHeight / 2.0));
      }, 1);
    }
    else
        window.scrollTo(0, scrollHeight - (windowHeight / 2.0));

    return;
  }

  return {
    'initialize': init,
    'parseHash': parseHash,
    'lastSelectedLineNumber': lastSelectedLineNumber,
    'supportsHistory': supportsHistory
  }
})();

var TabbedPastes = (function() {

  init = function() {

    this.tabs = $('[data-tab]');

    if(this.tabs.length == 0)
      return;

    this.hasTabs = true;
    this.pastes = $('[data-pasteid]');
    this.activePasteId = $('.active[data-tab]')[0].dataset.tab;

    var self = this;

    this.tabs.on('click', function() {

        var pasteId = $(this).data('tab');

        self.selectPasteWithId(pasteId);
    });
  },

  selectPasteWithId = function(pasteId) {

    if(this.activePasteId.localeCompare(pasteId) == 0)
        return;

    this.activePasteId = pasteId;

    $.each(this.tabs, function() {

        var tId = $(this).data('tab');

        if(tId.localeCompare(pasteId) == 0)
            $(this).addClass('active');
        else
            $(this).removeClass('active');
    });

    $.each(this.pastes, function() {

        var cId = $(this).data('pasteid');

        if(cId.localeCompare(pasteId) == 0) {

            var language = $(this).data('language');
            var expires = $(this).data('expires');
            var reporturl = $(this).data('reporturl');
            var rawurl = $(this).data('rawurl');

            $('[data-container-language]')[0].innerText = language;
            $('[data-container-expiration]')[0].innerText = expires;
            $('[data-container-report]')[0].action = reporturl;
            $('[data-container-raw]')[0].value = rawurl;

            $(this).attr('aria-hidden', '');
        }
        else
            $(this).attr('aria-hidden', 'true');
    });
  }

  return {
      'initialize': init,
      'selectPasteWithId': selectPasteWithId,
      'tabs': [],
      'pastes': [],
      'hasTabs': false,
      'activePasteId': ''
  }

})();

$(document).ready(function() {

  autosize($('textarea'));

  TabbedPastes.initialize();
  LineSelector.initialize();
  ConfirmAction.initialize();
  UserStyleSelector.initialize();
  ShareSelector.initialize();
});