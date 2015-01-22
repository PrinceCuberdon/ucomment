/*
 * UComment - Django Universal comment
 * (c) Prince Cuberdon 2015 and Later <princecuberdon@bandcochon.fr>
 */

var UComment = (function() {
    "use strict";

    var ProgressBar = (function() {
        function ProgressBar() {
            this._container = document.getElementById('ucomment-progress');
            if (!this._container) {
                return;
            }
            var element = document.createElement('div');
            element.classList.add('ucomment-progress-bar');
            element.setAttribute('value', '0');
            element.setAttribute('max', '100');
            this._container.appendChild(element);
            this._progressBar = element;
            this.hide();
        }

        ProgressBar.prototype.container = null;
        ProgressBar.prototype._progressBar = null;

        ProgressBar.prototype.update = function(v) {
            this.value = v;
            this._progressBar.style.width = ((parseFloat(this._progressBar.getAttribute('value')) / parseFloat(this._progressBar.getAttribute('max'))) * 100) + '%';
            this._progressBar.setAttribute('value', v);
        };

        ProgressBar.prototype.getValue = function() {
            return parseFloat(this._progressBar.getAttribute('value'));
        };

        ProgressBar.prototype.setValue = function(v) {
            this._progressBar.setAttribute('value', v);
        };

        ProgressBar.prototype.show = function() {
            this._container.style.display = 'block';
        };

        ProgressBar.prototype.hide = function() {
            this._container.style.display = 'none';
        };

        return ProgressBar;
    })();

    function UComment(options) {
        this._onError = 'error' in options ? options.error : function () {};
        this._onSuccess = 'success' in options ? options.success : function () {};
        this._onLoad = 'load' in options ? options.load : function () {};
        this._onFinish = 'finish' in options ? options.finish : function () {};
        this._onProgress = 'progress' in options ? options.progress : function () {};

        this._progressBar = new ProgressBar();
        var like_els = document.querySelectorAll('[data-ucomment-like]');
        var dislike_els = document.querySelectorAll('[data-ucomment-dislike]');
        var self = this, i, _l;

        for (i = 0, _l = like_els.length; i < _l; i++) {
            (function (el) {
                el.onclick = function (e) {
                    e.preventDefault();
                    self.put({
                        url: "/ucomment/like/" + e.target.getAttribute("data-ucomment-like") + "/",
                        target: e.target,
                        action: 'like'
                    });

                }
            })(like_els[i]);
        }
        for (i = 0, _l = dislike_els.length; i < _l; i++) {
            (function (el) {
                el.onclick = function (e) {
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
        for (i = 0, _l = abuse.length; i < _l; i++) {
            (function (el) {
                el.onclick = function (e) {
                    e.preventDefault();
                    self._reportAbuse({
                        url: '/ucomment/report/abuse/' + el.getAttribute('data-ucomment-report-abuse') + '/',
                        target: e.target,
                        action: 'report_abuse'
                    });
                }
            })(abuse[i]);
        }

        // Cleanup contentns
        var textareas = document.querySelectorAll('textarea.ucomment');
        for (i = 0, _l = textareas.length; i < _l; i++) {
            textareas[i].value = '';
        }
        // Connect form
        document.querySelector('form.ucomment').onsubmit = function (e) {
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

        // File upload
        document.querySelector('[name=ucomment-files]').value = '';
        document.querySelector('[name=ucomment-files]').addEventListener('change', function (evt)  {
            if (!window.FormData) {
                alert("IE 9 isn't supported yet!");
                return;
            }
            var inputFiles = this;

            if (this.files) {
                var fd = new FormData();
                for (var i in this.files) {
                    fd.append("files", this.files[i]);
                }
                self._sendAjax('POST', {
                    url: '/ucomment/send_files/',
                    action: 'upload',
                    target: evt.target,
                    onProgress: function(percent) {
                        self._progressBar.update(percent);
                    },
                    onFinish: function() {
                        inputFiles.value = null;
                        self._progressBar.hide();
                    },
                    onStart: function() {
                        self._progressBar.show();
                    }
                }, fd);
            }
        }, false);
    }

    UComment.prototype._progressBar = null;

    /** Put in ajax way
     * @param {Object} args The arguments that will be stringified
     */
    UComment.prototype.put = function (args) {
        this._sendAjax('PUT', args, null);
    };

    /** Post in ajax way
     */
    UComment.prototype.post = function (args) {
        this._sendAjax('POST', args, JSON.stringify({
            path: args.path,
            action: args.action,
            'ucomment-content': args.content
        }))

    };

    UComment.prototype.showProgressBar = function(b) {
        b === true ? this._progressBar.show() : this._progressBar.hide();
    };

    UComment.prototype._sendAjax = function (method, args, sending) {
        var xhr = new XMLHttpRequest();
        var self = this;

        xhr.addEventListener('readystatechange', function () {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    var resp = JSON.parse(xhr.responseText);
                    if (resp.success === false) {
                        if (args.onError && typeof args.onError === "function") {
                            args.onError(resp.message);
                        }

                        self._onError({
                            action: args.action,
                            target: args.target,
                            url: args.url,
                            success: false,
                            message: resp.message
                        });
                    } else {
                        if (args.onSuccess && typeof args.onSuccess === "function") {
                            args._onSuccess();
                        }

                        self._onSuccess({
                            action: args.action,
                            target: args.target,
                            url: args.url,
                            response: resp
                        });
                    }
                } else {
                    if (args.onError && typeof args.onError === "function") {
                        args.onError(resp.message);
                    }

                    self._onError({
                        action: args.action,
                        target: args.target,
                        url: args.url,
                        success: false,
                        message: resp.message
                    });
                }
                if (args.onFinish && typeof args.onFinish === "function") {
                    args.onFinish();
                }
                self._onFinish({action: args.action});
            }
        });

        xhr.addEventListener('progress', function (e) {
            var percent = ((e.loaded / e.total) * 100) | 0;

            if (args.onProgress && typeof args.onProgress === "function") {
                args.onProgress(percent);
            }

            self._onProgress({
                action: 'upload',
                loaded: e.loaded,
                total: e.total,
                percent: percent
            });
        }, false);

        xhr.addEventListener('error', function (e) {
            if (args.onError && typeof args.onError === "function") {
                args.onError(resp.message);
            }
            self._onError({
                action: args.action,
                target: args.target,
                url: args.url,
                success: false,
                message: xhr.responseText
            });
        }, false);

        xhr.addEventListener('load', function (e) {
            if (args.onLoad && typeof args.onLoad === "function") {
                args.onLoad();
            }

            self._onLoad({
                action: args.action,
                url: args.url,
                target: args.target
            });
        }, false);

        xhr.open(method.toUpperCase(), args.url, true);
        xhr.setRequestHeader("X-CSRFToken", this._getCookie('csrftoken'));
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        if (args.onStart && typeof args.onStart === "function") {
            args.onStart();
        }
        xhr.send(sending);
    };

    UComment.prototype._reportAbuse = function (args) {
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
    UComment.prototype._getCookie = function (name) {
        var cookies = document.cookie.split(';');
        for (var i = 0, _l = cookies.length; i < _l; i++) {
            var k = cookies[i].split('=');
            if (k[0] === name) {
                return k[1];
            }
        }
        return '';
    };

    return UComment;
})();

document.addEventListener("DOMContentLoaded", function() {
    var uc = new UComment({
        progress: function(args) {

        },

        error: function(args) {
            switch (args.action) {
                case 'like':
                case 'dislike':
                    alert('ERROR\n' +args.message);
                    break;
            }
        },

        load: function(args) {

        },

        finish: function(args) {
        },

        success: function(args) {
            switch (args.action) {
                case 'submit':
                    var container = document.querySelector("#ucomment-container");
                    container.innerHTML = args.response.content + container.innerHTML;
                    break;

                case 'like':
                case 'dislike':
                    document.getElementById('ucomment-likeit-' + args.response.pk).innerHTML = '' + args.response.like;
                    document.getElementById('ucomment-dislikeit-' + args.response.pk).innerHTML = ' ' + args.response.dislike;
                    break;

                case 'report_abuse':
                    args.target.remove();

            }
        }
    });
});

