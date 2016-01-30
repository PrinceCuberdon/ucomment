$(document).ready(function() {
	$("form#addcomment").live('submit', function(e) {
		e.preventDefault();
		var $textarea=$("form#addcomment textarea");
		var $me = $(this);
				
		if ($.trim($textarea.val()).length == 0) {
			return;
		}
        var $dest = $($(this).attr("data-dest"));
        var prepend = $('form#addcomment').attr("data-method") == 'prepend';
        
		$(this).slideUp(function() {
			$(".wait-comment").show();
			$.post($("form#addcomment").attr("action"), {
				onwall: $("form#addcomment").attr("data-wall"),
				onwallurl: $("form#addcomment").attr("data-wall-url"),
                content: $textarea.val()
			}, function(data) {
				if (prepend == true)
					$(data).prependTo($dest)
				else
			    	$(data).appendTo($dest);
			}).complete(function() {
                $me.slideDown();
                $textarea.val('');
                $(".wait-comment").hide();
			}).error(function() {
				$('<div class="error">Erreur de communication avec le serveur</div>').appendTo($dest);
				setTimeout(function() {$(".error").slideUp();}, 2000);
            });
		});
	});
	$("button.repondre").live('click', function() {
		var commentpk = $(this).attr("data-rel");
		if ($(this).attr("data-open") == "true") {
			$(".comment-response[data-rel="+commentpk+"]").slideUp();
			$(this).html('Répondre').attr("data-open", "false");
		} else {
			$(".comment-response[data-rel="+commentpk+"]").slideDown();
			$(this).html('Fermer').attr("data-open", "true");
			$("textarea[data-rel="+commentpk+"]").focus();
		}
		$("textarea[data-rel="+commentpk+"]").val('');
	});
	$("button.close-response").live('click', function() {
		$("textarea[data-rel="+$(this).attr('data-rel')+"]").val('');
		$(".comment-response[data-rel="+$(this).attr('data-rel')+"]").slideUp();
		$("button.repondre").html('Répondre').attr("data-open", "false");		
	});
	$("button.send-response").live('click', function() {
		var datarel = $(this).attr("data-rel");
		var content = $("textarea[data-rel="+datarel+"]").val();
		$(".wait-response[data-rel="+datarel+"]").show();
		$(".comment-response[data-rel="+datarel+"]").slideUp();
		var action = $("form#addcomment").attr("action");
		$.post(action, {
			//onwall: $("form#addcomment").attr("data-wall"),
			onwallurl: $("form#addcomment").attr("data-wall-url"),
			parent: datarel,
			content: content,
			onwall: $("textarea[data-rel="+datarel+"]").data('wall')
		}, function(data) {
			$(data).hide();
			$(data).appendTo($(".message-response[data-rel="+datarel+"]"));
			$(data).slideDown();
		}).complete(function() {
			$(".wait-response").hide();
			$("textarea[data-rel="+datarel+"]").val('');
			$('button.repondre[data-rel='+datarel+']').html('Répondre').attr("data-open", "false");		
		}).error(function() {
			$('<div class="error">Erreur de communication avec le serveur</div>').appendTo($(".message-response[data-rel="+datarel+"]"));
			setTimeout(function() {$(".error").slideUp();}, 2000);
		});
	});
	
    function setVoteMessage(rel, msg) {
		$who = $(".message-comment[data-rel="+rel+"]");
		$who.html(msg).animate({
		    opacity: 1.0
		}, 700, function(){
		    setTimeout(function() {
				$who.html('');
		    }, 1000);
		});
    }
    
    agree_or_not = function(ag, rel, onwall, onwallurl) {
        $("span.wait[data-rel="+rel+"]").show();
        $.post('/ucomment/'+ag+'/', { 
        		'message' : rel,
        		onwall:onwall,
        		onwallurl: onwallurl
        	}, function(data) {
		    if (data == -1) {
				setVoteMessage(rel, "<span class='error'>Vous ne pouvez plus voter pour ce message</span>");
		    } else {
				setVoteMessage(rel, "Votre vote a été pris en compte");
		        $("."+ag+"-count[data-rel="+rel+"]").text(data);
		    }
        }).error(function() {
	    	setVoteMessage(rel, "<span class='error'>Erreur de communication avec le serveur</span>");
        }).complete(function() {
            $("span.wait[data-rel="+rel+"]").hide();
        });
    }
    
    $(".agree-count").live('click', function() {
        agree_or_not('agree', $(this).attr('data-rel'), $(this).attr("data-wall"), $(this).attr("data-wall-url"));
    });
    $(".disagree-count").live('click', function() {
        agree_or_not('disagree', $(this).attr('data-rel'), $(this).attr("data-wall"), $(this).attr("data-wall-url"));
    });
    
    $(".agree-count").live('hover', function() {
        rel = $(this).attr('data-rel');
        $(".comment-user[data-rel="+rel+"][data-role=likeit]").slideToggle(250);
    }, function() {$(".comment-user[data-role=likeit]").slideToggle(250);});
    
    $(".disagree-count").live('hover', function() {
        rel = $(this).attr('data-rel');
        $(".comment-user[data-rel="+rel+"][data-role=dislikeit]").slideToggle(250);
    }, function() {$(".comment-user[data-role=dislikeit]").slideToggle(250);});
    
    $(".moderate-comment").live('click', function(e) {
    	e.preventDefault();
    	var signal = $(this).attr("data-user") == "true";
    	var rel = $(this).attr("data-rel");
    	var href = $(this).attr("href");
    	
    	if (signal) {
	    	$('div[data-rel='+rel+']')
	    		.slideUp(function() {
	    			$(".comment-user[data-rel="+rel+"]").remove();
	    			$(this)
	    				.css('backgroundColor','#FFA7F0')
	    				.html('<div style="padding: 5px; font-weight: bold;">Message en attente de modération</div>')
	    				.slideDown();
		    	});
			$("<div>&nbsp;</div>").insertAfter($("div[data-rel="+rel+"]"));
		} else {
			$(this).parent().html("Merci de votre participation");
		}
	    $.post(href, { rel:rel});
	});
	
	$(".next-group").live('click', function() {
		$(".wait-comments").show();
		$.get('/ucomment/nextcomment/', {
			startat: currentComment,
			url: '/'
		}, function(data) {
			$(".next-comments").remove();
			$(data).hide();
			$(data).appendTo($(".messages-content"));
			$(data).slideDown();
		}).complete(function() {
			$(".wait-comments").hide();
			currentComment = $('a[name]').size();
		});
	});

	currentComment = $('a[name]').size();
	        
});
