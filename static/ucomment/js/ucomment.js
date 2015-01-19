/*
 * UComment - Django Universal comment
 * (c) Prince Cuberdon 2015 and Later <princecuberdon@bandcochon.fr>
 */

var UComment = (function() {
    "use strict";
    
    function UComment(options) {
        this.onerror = 'error' in options ? options.error : function() {};
        this.onsuccess = 'success' in options ? options.success : function() {};
        this.onload = 'load' in options ? options.load : function() {};
        this.onfinish = 'finish' in options ? options.finish : function() {};

        var like_els = document.querySelectorAll('[data-ucomment-like]');
        var dislike_els = document.querySelectorAll('[data-ucomment-dislike]');
        var self = this;
        var i= 0;
        var _l=0;

        for (i=0,_l=like_els.length; i<_l; i++) {
            (function(el) {
                el.onclick = function(e) {
                    e.preventDefault();
                    self.put({
                        url: "/ucomment/like/" + e.target.getAttribute("data-ucomment-like") + "/",
                        target: e.target,
                        action: 'like'
                    });
                }                
            })(like_els[i]);
        }
        for (i=0,_l=dislike_els.length; i<_l; i++) {
            (function(el) {
                el.onclick = function(e) {
                    e.preventDefault();
                    self.put({
                        url: "/ucomment/dislike/" + e.target.getAttribute("data-ucomment-dislike") + "/",
                        target: e.target,
                        action: 'dislike'
                    });
                }                
            })(dislike_els[i]);
        }

        var abuse = document.querySelectorAll('[data-ucomment-report-abuse]');
        for(i=0, _l=abuse.length; i < _l; i++) {
            (function(el) {
                el.onclick = function(e) {
                    e.preventDefault();
                    self.reportAbuse({
                        url: '/ucomment/report/abuse/' + el.getAttribute('data-ucomment-report-abuse') + '/',
                        target: e.target,
                        action: 'report_abuse'
                    });
                }
            })(abuse[i]);
        }
        
        // Cleanup contentns
        var textareas = document.querySelectorAll('textarea.ucomment');
        for(i=0,_l=textareas.length;i<_l;i++) {
            textareas[i].value = '';
        }
        
        // Connect form
        document.querySelector('form.ucomment').onsubmit = function(e) {
            if (this.querySelector('textarea').value.trim() === '')
                return false;
            
            e.preventDefault();
            
            self.post({
                url: this.getAttribute('action'),
                content: this.querySelector('[name="ucomment-content"]').value,
                path: this.querySelector('[name="ucomment-path"]').value,
                target: e.target,
                action: 'submit'
            });
            this.querySelector('[name="ucomment-content"]').value = '';
            return false;
        };
    }    
    
    /** Put in ajax way
     * @param {Object} args The arguments that will be stringified
    */
    UComment.prototype.put = function(args) {
        this._sendAjax('PUT', args, null);
/*        var xhr = new XMLHttpRequest(), self=this;
        xhr.onreadystatechange = function(e) {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    var resp = JSON.parse(xhr.responseText);
                    if (resp.success === false) {
                        self.onerror({action: args.action, target: args.target, url: args.url, success: false, message: resp.message});
                    } else {
                        self.onsuccess({action: args.action, target: args.target, url: args.url, response: resp});
                    }
                } else {
                    self.onerror({action: args.action, target: args.target, url: args.url, success: false, message: resp.message});
                }
                
                self.onfinish({action: args.action});
            }
        };
        
        xhr.onerror = function(e) {
            self.onerror({action: args.action, target: args.target, url: args.url, success: false, message: xhr.responseText});

        };
        xhr.onload = function(e) {
            self.onload({
                action: args.action,
                url: args.url,
                target: args.target
            });
        };
        
        xhr.open('PUT', args.url);
        xhr.setRequestHeader("X-CSRFToken", this._getCookie('csrftoken'));
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')

        xhr.send(null);*/
    };
    
    /** Post in ajax way
     * @param {String} url The url where to send PUT
     * @param {Object} args The arguments that will be stringified
    */
    UComment.prototype.post = function(args) {
        this._sendAjax('POST', args, JSON.stringify({
            path: args.path,
            action: args.action,
            'ucomment-content': args.content
        }));
    };

    UComment.prototype._sendAjax = function(method, args, sending) {
        var xhr = new XMLHttpRequest();
        var self = this;

        xhr.onreadystatechange = function(e) {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    var resp = JSON.parse(xhr.responseText);
                    if (resp.success === false) {
                        self.onerror({
                            action: args.action,
                            target: args.target,
                            url: args.url,
                            success: false,
                            message: resp.message
                        });
                    } else {
                        self.onsuccess({
                            action: args.action,
                            target: args.target,
                            url: args.url,
                            response: resp
                        });
                    }
                } else {
                    self.onerror({
                        action: args.action,
                        target: args.target,
                        url: args.url,
                        success: false,
                        message: resp.message
                    });
                }
                self.onfinish({action: args.action});
            }
        };

        xhr.onerror = function(e) {
            self.onerror({action: args.action, target: args.target, url: args.url, success: false, message: xhr.responseText});

        };
        xhr.onload = function(e) {
            self.onload({
                action: args.action,
                url: args.url,
                target: args.target
            });
        };

        xhr.open(method.toUpperCase(), args.url);
        xhr.setRequestHeader("X-CSRFToken", this._getCookie('csrftoken'));
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        xhr.send(sending);
    };

    UComment.prototype.reportAbuse = function(args) {
        this._sendAjax('GET', {
            action: args.action,
            url: args.url,
            target: args.target
        }, null);
    };
    
    /**
     * Get a Cookie
     * @param {String} name The cookie name
     * @returns {String} The cookie value
     */
    UComment.prototype._getCookie = function(name) {
        var cookies = document.cookie.split(';');
        for(var i=0,_l=cookies.length; i < _l; i++) {
            var k = cookies[i].split('=');
            if (k[0] === name) {
                return k[1];
            }
        }
        return '';
    };
    
    return UComment;
})();

document.addEventListener("DOMContentLoaded", function(evt) {
    var uc = new UComment({
        error: function(args) {
            if (args.action == 'like' || args.action == 'dislike') {
                alert("ERROR\n" +args.message);
            }
        },
        
        load: function(args) {
            if (args.action == 'submit') {
                console.log('un instant');
            }
        },
        
        finish: function(args) {
            if (args.action == 'submit') {
                console.log('C fait')
            }
        },
        
        success: function(args) {
            switch (args.action) {
                case 'submit':
                    var container = document.querySelector("#ucomment-container");
                    container.innerHTML = args.response.content + container.innerHTML;
                    break;

                case 'like':
                case 'dislike':
                    document
                        .getElementById('ucomment-likeit-' + args.response.pk).innerHTML = '' + args.response.like;
                    document
                        .getElementById('ucomment-dislikeit-' + args.response.pk).innerHTML = ' ' + args.response.dislike;
                    break;

                case 'report_abuse':
                    args.target.remove();

            }
        }
    });
});

