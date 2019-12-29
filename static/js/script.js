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
      else
        self.changeStyle();
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

var BurgerButton = (function() {

  init = function() {

    if($('.burger-button').length == 0)
      return;

    $('.burger-button').on('click', function() {

        $(this).toggleClass('open');
        $('.paste .button-container').toggleClass('open');
    });
  }

  return {
      'initialize': init
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

    if($('.page-paste').length == 0)
        return;

    $('.linenos pre').attr('aria-hidden', 'true');
    $.each($('.linenos pre a:not(:first-child)'), function() { this.setAttribute('tabindex', '-1'); });

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

    if(hash.indexOf('#l-') < 0) {

        if(hash.indexOf('#') == 0) {

            var pasteId = hash.split('#')[1];

            if(pasteId && pasteId.length > 0)
                TabbedPastes.selectPasteWithId(pasteId);
        }

        return;
    }

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

    if($('.page-paste').length == 0)
        return;

    this.applyActivePaste();

    this.tabs = $('[data-tab]');

    if(this.tabs.length == 0)
      return;

    this.tabsParent = $('h1.tabs')[0];
    this.tabArrows = $('[data-arrow]');

    this.hasTabs = true;
    this.pastes = $('[data-pasteid]');
    this.activePasteId = this.tabs[0].dataset.tab;

    this.hasPlus = (document.querySelector('.plus') != null);

    this.pasteIds = [];

    for(var i = 0; i < this.pastes.length; i++)
      this.pasteIds.push(this.pastes[i].dataset.pasteid);

    var self = this;

    if(this.hasPlus) {

        document.querySelector('.plus').addEventListener('click', function() {

            localStorage.otherPastes = self.pasteIds.join(',');
            location.href = '/';
        });
    }

    this.tabs.on('click', function() {

        var pasteId = $(this).data('tab');

        if(!pasteId || pasteId == '')
            return;

        var url = '#' + pasteId;

        history.pushState(null, null, url);

        self.selectPasteWithId(pasteId);
    });

    $.each(this.tabArrows, function() {

        $(this).on('click', function() {

            var data = parseInt($(this).data('arrow'));

            if(data == -1)
                self.tabsParent.scrollLeft = 0;
            else
                self.tabsParent.scrollLeft = self.tabsParent.scrollWidth - self.tabsParent.clientWidth;
        });
    });

    window.addEventListener('resize', this.resized.bind(this));

    this.resized();
  },

  resized = function() {

    var tabsWidth = 0;

    $.each(this.tabs, function() {

        tabsWidth += this.clientWidth + 4;
    });

    if(this.hasPlus)
        tabsWidth += 35;

    var hasArrows = $(this.tabsParent.parentElement).hasClass('enabled');
    var shouldShowArrows = (this.tabsParent.clientWidth <= tabsWidth);

    if(hasArrows == shouldShowArrows)
        return;

    if(shouldShowArrows)
        $(this.tabsParent.parentElement).addClass('enabled');
    else
        $(this.tabsParent.parentElement).removeClass('enabled');
  },

  selectPasteWithId = function(pasteId) {

    if(this.activePasteId.localeCompare(pasteId) == 0)
        return;

    if(this.pasteIds.indexOf(pasteId) < 0)
        return;

    var hasActivated = false;

    $.each(this.tabs, function() {

        var tId = $(this).data('tab');

        if(tId.localeCompare(pasteId) == 0) {

            if(!hasActivated) {

                $(this).addClass('active');
                hasActivated = true;
            }
        }
        else
            $(this).removeClass('active');
    });

    if(!hasActivated)
        return;

    this.activePasteId = pasteId;

    hasActivated = false;

    $.each(this.pastes, function() {

        var cId = $(this).data('pasteid');

        if(cId.localeCompare(pasteId) == 0) {

            if(!hasActivated) {

                $(this).attr('aria-hidden', 'false');
                hasActivated = true;
            }
        }
        else
            $(this).attr('aria-hidden', 'true');
    });

    this.applyActivePaste();
  },

  applyActivePaste = function() {

    var paste = document.querySelector('.pretty-paste[aria-hidden="false"]');

    var language = $(paste).data('language');
    var expires = $(paste).data('expires');
    var rawurl = $(paste).data('rawurl');
    var cloneurl = $(paste).data('cloneurl');

    var notFound = $(paste).hasClass('not-found');

    if(notFound) {
      $('.copy-clipboard').addClass('disabled');
      $('.copy-clipboard+.pseudo-dropdown .btn-group')[0].innerText = 'Not available';
    }
    else {
      $('.copy-clipboard').removeClass('disabled');
      $('.copy-clipboard+.pseudo-dropdown .btn-group')[0].innerText = 'Copy to clipboard';
    }

    $('[data-container-language]')[0].innerText = language;
    $('[data-container-expiration]')[0].innerText = expires;

    if(!notFound) {

      $('.meta-footer')[0].style.display = 'block';
    }
    else {

      $('.meta-footer')[0].style.display = 'none';
    }

    if(!notFound) {

      $('[data-container-raw]')[0].value = rawurl;
      $('[data-raw]')[0].disabled = '';
    }
    else {

      $('[data-container-raw]')[0].value = 'Not available';
      $('[data-raw]')[0].disabled = 'disabled';
    }

    if(!notFound) {

      $('.clone').removeClass('disabled');
      $('.clone')[0].href = cloneurl;
      $('.clone+.pseudo-dropdown')[0].innerText = 'Clone';
    }
    else {

      $('.clone').addClass('disabled');
      $('.clone')[0].href = 'javascript:void(0);';
      $('.clone+.pseudo-dropdown')[0].innerText = 'Not available';
    }

    $(this).attr('aria-hidden', 'false');
  }

  return {
      'initialize': init,
      'selectPasteWithId': selectPasteWithId,
      'applyActivePaste': applyActivePaste,
      'resized': resized,
      'tabs': [],
      'pastes': [],
      'hasTabs': false,
      'activePasteId': ''
  }

})();

var CopyToClipboard = (function() {

  init = function() {

    var self = this;

    var support = !!document.queryCommandSupported;
    support = support && !!document.queryCommandSupported('copy');

    if(!support) {

      $('.copy-clipboard').each(function() { this.parentElement.style.display = 'none'; })
      return;
    }

    $('.copy-clipboard').on('click', function() {

      var element = $(this);

      var paste= document.querySelector('.pretty-paste[aria-hidden="false"]');
      var hasMarkdown = (paste.className.indexOf('markdown-language') > 0);
      var code = '';

      if(hasMarkdown)
          code = paste.innerText;
      else {

        var preElement = document.querySelector('.pretty-paste[aria-hidden="false"] .code pre');

        if(!preElement)
          return;

        code = preElement.innerText;
      }

      var copied = self.copyTextToClipboard(code);

      if(copied) {

        $(element).tooltip({title: 'Copied!'});
        $(element).tooltip('show');

        setTimeout(function() {

          $(element).tooltip('destroy');

        }, 1000);
      }
    });
  },

  removeFake = function() {

    if (this.fakeHandler) {

      document.body.removeEventListener('click', this.fakeHandlerCallback);
      this.fakeHandler = null;
      this.fakeHandlerCallback = null;
    }

    if (this.fakeElem) {

      document.body.removeChild(this.fakeElem);
      this.fakeElem = null;
    }
  },

  copyTextFromElement = function(element) {

    element.select();
    element.setSelectionRange(0, element.value.length);

    var succeeded = false;

    try {
      succeeded = document.execCommand('copy');
    }
    catch (err) {
      succeeded = false;
    }

    return succeeded;
  },

  copyTextToClipboard = function(text){

    this.removeFake();

    var self = this;

    this.fakeHandlerCallback = function() { self.removeFake(); };

    this.fakeHandler = document.body.addEventListener('click', this.fakeHandlerCallback) || true;

    this.fakeElem = document.createElement('textarea');
    this.fakeElem.style.fontSize = '12pt';
    this.fakeElem.style.border = '0';
    this.fakeElem.style.padding = '0';
    this.fakeElem.style.margin = '0';
    this.fakeElem.style.position = 'absolute';
    this.fakeElem.style[ document.documentElement.getAttribute('dir') == 'rtl' ? 'right' : 'left' ] = '-9999px';
    this.fakeElem.style.top = (window.pageYOffset || document.documentElement.scrollTop) + 'px';
    this.fakeElem.setAttribute('readonly', '');
    this.fakeElem.value = text;

    document.body.appendChild(this.fakeElem);

    return this.copyTextFromElement(this.fakeElem);
  }

  return {
    'initialize': init,
    'copyTextToClipboard': copyTextToClipboard,
    'copyTextFromElement': copyTextFromElement,
    'removeFake': removeFake
  }
})();

var PasteryForm = (function() {

  initialize = function() {

    this.formElement    = document.querySelector('.pastery-form');
    this.idWorkElement  = document.querySelector('#id_work');
    this.textareaElement= document.querySelector('#id_body');

    if(!this.formElement)
      return;

    var self = this;

    if(this.idWorkElement)
      this.idWorkElement.value = 'I\'m not a bot, promise';

    if(this.textareaElement) {

      autosize(this.textareaElement);

      this.textareaElement.addEventListener('keydown', function(e) {

        if(this.value.trim() == '')
          return;

        if ((e.ctrlKey || e.metaKey) && (e.keyCode == 13 || e.keyCode == 10))
          self.submitForm();
      });
    }

    if(localStorage.otherPastes && localStorage.otherPastes != '') {

      var otherPastesInput = document.createElement('input');
      otherPastesInput.id = 'id_other_pastes';
      otherPastesInput.name = 'other_pastes';
      otherPastesInput.value = localStorage.otherPastes;
      otherPastesInput.type = 'hidden';

      localStorage.removeItem('otherPastes');

      this.formElement.appendChild(otherPastesInput);
    }

    this.formElement.addEventListener('submit', function(event) {

      event.preventDefault();

      self.submitForm();
    });
  },

  submitForm = function() { this.formElement.submit(); }

  return {
    'initialize': initialize,
    'submitForm': submitForm
  }
})();

var AuthenticationTypeSelector = (function() {

  var init = function() {

    if(document.querySelector('.authentication-methods') == null)
      return;

    let authenticationTips = [...document.querySelectorAll('.authentication-tips > div')];

    [...document.querySelectorAll('.authentication-type button')].forEach(element => {

      element.addEventListener('mouseenter', function() {

        authenticationTips.forEach(element => { element.style.display = 'none'; });

        document.querySelector('.authentication-tips [data-caption="'+this.dataset['action']+'"]').style.display = 'block';
      });

      element.addEventListener('mouseleave', function() {

        authenticationTips.forEach(element => { element.style.display = 'none'; });

        document.querySelector('.authentication-tips [data-caption="none"]').style.display = 'flex';
      });
    });

    document.querySelector('.authentication-methods button[data-action="email"]').addEventListener('click', () => {
      document.querySelector('.authentication-methods').style.display = 'none';
      document.querySelector('.login-container[data-section="email"]').style.display = 'block';
    });

    document.querySelector('.login-container a[data-action="back"]').addEventListener('click', () => {
      document.querySelector('.authentication-methods').style.display = 'block';
      document.querySelector('.login-container[data-section="email"]').style.display = 'none';      
    })
  }

  return {
    'initialize': init
  }
})();

$(document).ready(function() {

    BurgerButton.initialize();
    CopyToClipboard.initialize();
    PasteryForm.initialize();
    TabbedPastes.initialize();
    LineSelector.initialize();
    ConfirmAction.initialize();
    UserStyleSelector.initialize();
    ShareSelector.initialize();
    AuthenticationTypeSelector.initialize();
});