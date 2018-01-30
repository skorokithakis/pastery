"use strict";

(function() {

    var PasteList = {

        'initialize' : function() {

            var pasteElements = document.getElementsByClassName('paste-list');

            if(!pasteElements.length)
                return;

            window.addEventListener("message", function(message) {

                var iframeId = message.data['paste-id'];
                var iframeHeight = message.data['height'];

                document.getElementById('pasteid-' + iframeId) && (document.getElementById('pasteid-' + iframeId).style.height = iframeHeight + 'px');

            }, false);

            for(var i = 0; i < pasteElements.length; i++) {

                if(pasteElements[i].hasAttribute('data-pasteid'))
                    this.setup(pasteElements[i]);
            }
        },

        'setup' : function(pasteElement) {

            var iframe = document.createElement('iframe');

            var pasteid = pasteElement.getAttribute('data-pasteid');
            var src = "https://www.pastery.net/";

            iframe.id = 'pasteid-' + pasteid;
            iframe.src = src + pasteid + '/embed/?host=' + window.location.href;

            iframe.style.border = 'none';
            iframe.style.height = '300px';
            iframe.style.width = '100%';
            iframe.style.overflow = 'hidden';
            iframe.style.verticalAlign = 'bottom';

            iframe.setAttribute('allowTransparency', true);
            iframe.setAttribute('frameBorder', 0);
            iframe.setAttribute('tabIndex', 0);
            iframe.setAttribute('scrolling', 'yes');

            pasteElement.appendChild(iframe);
        }
    };

    PasteList.initialize();

})();
